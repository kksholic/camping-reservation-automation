"""
Session Warmup 서비스

예약 시간 전에 모든 계정을 미리 로그인하고 세션을 유지하여
예약 시점에 로그인 시간 손실 없이 즉시 예약 가능하도록 합니다.
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from app.models.database import CampingSiteAccount, CampingSite
from app.scrapers.xticket_scraper import XTicketScraper
from app.utils.time_sync import PreciseTimeSync, get_time_sync


class SessionState(Enum):
    """세션 상태"""
    IDLE = "idle"  # 대기 중
    WARMING = "warming"  # 워밍업 중
    READY = "ready"  # 준비 완료
    EXPIRED = "expired"  # 만료됨
    FAILED = "failed"  # 실패


@dataclass
class AccountSession:
    """계정 세션 정보"""
    account_id: int
    account: CampingSiteAccount
    scraper: Optional[XTicketScraper] = None
    state: SessionState = SessionState.IDLE
    last_activity: Optional[datetime] = None
    login_time: Optional[datetime] = None
    error_message: Optional[str] = None

    def is_ready(self) -> bool:
        return self.state == SessionState.READY and self.scraper is not None

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        if self.last_activity is None:
            return True
        elapsed = (datetime.utcnow() - self.last_activity).total_seconds() / 60
        return elapsed > timeout_minutes


class SessionWarmupService:
    """
    세션 워밍업 서비스

    Features:
    - 예약 시간 전 자동 로그인
    - 주기적 heartbeat로 세션 유지
    - 세션 만료 시 자동 재로그인
    - 서버 시간 동기화 연동
    """

    # 싱글톤 인스턴스
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._sessions: Dict[int, AccountSession] = {}  # schedule_id -> AccountSession dict
        self._heartbeat_threads: Dict[int, threading.Thread] = {}
        self._stop_events: Dict[int, threading.Event] = {}
        self._time_syncs: Dict[int, PreciseTimeSync] = {}

        # 설정
        self.heartbeat_interval = 60  # 초
        self.session_timeout = 30  # 분
        self.warmup_minutes_before = 5  # 예약 전 워밍업 시작 시간

        logger.info("SessionWarmupService initialized")

    def warmup_for_schedule(
        self,
        schedule_id: int,
        camping_site: CampingSite,
        accounts: List[CampingSiteAccount],
        execute_at: datetime
    ) -> Dict[int, AccountSession]:
        """
        스케줄에 대한 세션 워밍업 시작

        Args:
            schedule_id: 예약 스케줄 ID
            camping_site: 캠핑장 정보
            accounts: 로그인할 계정 목록
            execute_at: 예약 실행 시간

        Returns:
            계정별 세션 딕셔너리
        """
        logger.info(f"🔥 Starting session warmup for schedule #{schedule_id}")
        logger.info(f"   Camping site: {camping_site.name}")
        logger.info(f"   Accounts: {len(accounts)}")
        logger.info(f"   Execute at: {execute_at}")

        # 캠핑장 정보 파싱
        shop_encode, shop_code = self._parse_camping_site_url(camping_site.url)

        # 시간 동기화 초기화
        time_sync = get_time_sync(XTicketScraper.BASE_URL, shop_encode)
        time_sync.sync()
        self._time_syncs[schedule_id] = time_sync

        # 세션 저장소 초기화
        self._sessions[schedule_id] = {}
        self._stop_events[schedule_id] = threading.Event()

        # 각 계정 로그인
        threads = []
        for account in accounts:
            thread = threading.Thread(
                target=self._login_account,
                args=(schedule_id, account, shop_encode, shop_code),
                name=f"Login-{account.id}"
            )
            threads.append(thread)
            thread.start()

        # 모든 로그인 완료 대기
        for thread in threads:
            thread.join(timeout=30)

        # 결과 요약
        sessions = self._sessions[schedule_id]
        ready_count = sum(1 for s in sessions.values() if s.is_ready())
        failed_count = len(sessions) - ready_count

        logger.info(f"✅ Session warmup complete: {ready_count} ready, {failed_count} failed")

        # Heartbeat 시작
        self._start_heartbeat(schedule_id)

        return sessions

    def _login_account(
        self,
        schedule_id: int,
        account: CampingSiteAccount,
        shop_encode: str,
        shop_code: str
    ):
        """단일 계정 로그인"""
        session = AccountSession(
            account_id=account.id,
            account=account,
            state=SessionState.WARMING
        )
        self._sessions[schedule_id][account.id] = session

        try:
            # 스크래퍼 생성
            scraper = XTicketScraper(shop_encode, shop_code)

            # 로그인 시도
            logger.info(f"🔑 Logging in: {account.nickname or account.login_username}")

            success = scraper.login(account.login_username, account.login_password)

            if success:
                session.scraper = scraper
                session.state = SessionState.READY
                session.login_time = datetime.utcnow()
                session.last_activity = datetime.utcnow()
                logger.success(f"✅ Login successful: {account.nickname or account.login_username}")
            else:
                session.state = SessionState.FAILED
                session.error_message = "Login failed"
                logger.error(f"❌ Login failed: {account.nickname or account.login_username}")

        except Exception as e:
            session.state = SessionState.FAILED
            session.error_message = str(e)
            logger.error(f"❌ Login error for {account.nickname}: {e}")

    def _start_heartbeat(self, schedule_id: int):
        """Heartbeat 스레드 시작"""
        if schedule_id in self._heartbeat_threads:
            return

        thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(schedule_id,),
            name=f"Heartbeat-{schedule_id}",
            daemon=True
        )
        self._heartbeat_threads[schedule_id] = thread
        thread.start()

        logger.info(f"💓 Heartbeat started for schedule #{schedule_id}")

    def _heartbeat_loop(self, schedule_id: int):
        """Heartbeat 루프"""
        stop_event = self._stop_events.get(schedule_id)

        while stop_event and not stop_event.is_set():
            try:
                self._perform_heartbeat(schedule_id)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            # 다음 heartbeat까지 대기
            if stop_event:
                stop_event.wait(timeout=self.heartbeat_interval)

        logger.info(f"💔 Heartbeat stopped for schedule #{schedule_id}")

    def _perform_heartbeat(self, schedule_id: int):
        """Heartbeat 수행 (세션 유지)"""
        sessions = self._sessions.get(schedule_id, {})

        for account_id, session in sessions.items():
            if session.state != SessionState.READY or session.scraper is None:
                continue

            try:
                # 간단한 API 호출로 세션 유지
                server_time = session.scraper.get_server_time()

                if server_time:
                    session.last_activity = datetime.utcnow()
                    logger.debug(f"💓 Heartbeat OK: account {account_id}")
                else:
                    # 세션 만료 가능성 - 재로그인 시도
                    logger.warning(f"⚠️ Heartbeat failed for account {account_id}, re-logging in...")
                    self._relogin_account(schedule_id, session)

            except Exception as e:
                logger.warning(f"⚠️ Heartbeat exception for account {account_id}: {e}")
                session.state = SessionState.EXPIRED

    def _relogin_account(self, schedule_id: int, session: AccountSession):
        """계정 재로그인"""
        try:
            account = session.account
            logger.info(f"🔄 Re-logging in: {account.nickname or account.login_username}")

            if session.scraper:
                success = session.scraper.login(
                    account.login_username,
                    account.login_password
                )

                if success:
                    session.state = SessionState.READY
                    session.last_activity = datetime.utcnow()
                    logger.success(f"✅ Re-login successful")
                else:
                    session.state = SessionState.FAILED
                    logger.error(f"❌ Re-login failed")

        except Exception as e:
            session.state = SessionState.FAILED
            session.error_message = str(e)
            logger.error(f"❌ Re-login error: {e}")

    def get_ready_scrapers(self, schedule_id: int) -> Dict[int, XTicketScraper]:
        """준비된 스크래퍼 딕셔너리 반환"""
        sessions = self._sessions.get(schedule_id, {})
        return {
            account_id: session.scraper
            for account_id, session in sessions.items()
            if session.is_ready() and session.scraper is not None
        }

    def get_session_status(self, schedule_id: int) -> Dict:
        """세션 상태 조회"""
        sessions = self._sessions.get(schedule_id, {})

        status_list = []
        for account_id, session in sessions.items():
            status_list.append({
                'account_id': account_id,
                'nickname': session.account.nickname or session.account.login_username,
                'state': session.state.value,
                'login_time': session.login_time.isoformat() if session.login_time else None,
                'last_activity': session.last_activity.isoformat() if session.last_activity else None,
                'error_message': session.error_message
            })

        ready_count = sum(1 for s in sessions.values() if s.is_ready())

        return {
            'schedule_id': schedule_id,
            'total_accounts': len(sessions),
            'ready_count': ready_count,
            'failed_count': len(sessions) - ready_count,
            'accounts': status_list
        }

    def stop_warmup(self, schedule_id: int):
        """워밍업 중단 및 리소스 정리"""
        logger.info(f"🛑 Stopping warmup for schedule #{schedule_id}")

        # Heartbeat 중단
        if schedule_id in self._stop_events:
            self._stop_events[schedule_id].set()

        # 세션 정리
        sessions = self._sessions.get(schedule_id, {})
        for session in sessions.values():
            if session.scraper:
                try:
                    session.scraper.logout()
                except Exception:
                    pass

        # 리소스 해제
        if schedule_id in self._sessions:
            del self._sessions[schedule_id]
        if schedule_id in self._stop_events:
            del self._stop_events[schedule_id]
        if schedule_id in self._heartbeat_threads:
            del self._heartbeat_threads[schedule_id]
        if schedule_id in self._time_syncs:
            del self._time_syncs[schedule_id]

        logger.info(f"✅ Warmup stopped and resources released")

    def get_time_sync(self, schedule_id: int) -> Optional[PreciseTimeSync]:
        """해당 스케줄의 시간 동기화 객체 반환"""
        return self._time_syncs.get(schedule_id)

    def _parse_camping_site_url(self, url: str) -> tuple:
        """
        캠핑장 URL에서 shop_encode, shop_code 추출

        URL 형식: https://camp.xticket.kr/web/main?shopEncode=xxx
        """
        import re
        from urllib.parse import urlparse, parse_qs

        # URL 파싱
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        shop_encode = query_params.get('shopEncode', [''])[0]

        # shop_code는 별도 저장된 값 사용 또는 기본값
        # 실제 구현에서는 캠핑장 모델에 저장된 값 사용
        shop_code = "622830018001"  # 기본값 (생림오토캠핑장)

        if not shop_encode:
            # URL에서 직접 추출 시도
            match = re.search(r'shopEncode=([^&]+)', url)
            if match:
                shop_encode = match.group(1)

        logger.debug(f"Parsed URL: shop_encode={shop_encode}, shop_code={shop_code}")

        return shop_encode, shop_code


# 싱글톤 인스턴스
session_warmup_service = SessionWarmupService()
