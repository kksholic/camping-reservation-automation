"""
멀티 계정 동시 예약 서비스 (고도화 버전)

여러 계정으로 동시에 예약을 시도하는 서비스
- Wave Attack: 계정별 시차 발송
- Burst Retry: ms 단위 즉시 재시도
- Pre-fire: RTT 보상 선행 발송
- Session Warmup: 사전 로그인
- Priority Seat Pool: 다중 좌석 폴백
"""
import threading
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.models.database import CampingSite, CampingSiteAccount, CampingSiteSeat, Reservation
from app import db
from app.scrapers.xticket_scraper import XTicketScraper
from app.utils.time_sync import PreciseTimeSync, PreciseWaiter, get_time_sync
from app.services.wave_attack_service import (
    WaveAttackService, WaveAttackConfig, BurstRetryConfig, AdvancedReservationService
)
from app.services.session_warmup_service import session_warmup_service


class AccountReservationResult:
    """계정별 예약 결과"""
    def __init__(self, account_id: int, account_nickname: str, login_username: str):
        self.account_id = account_id
        self.account_nickname = account_nickname
        self.login_username = login_username
        self.success = False
        self.reservation_number = None
        self.selected_seat = None
        self.error_message = None
        self.completed_at = None
        self.attempts = 0
        self.duration_ms = 0

    def to_dict(self):
        return {
            'account_id': self.account_id,
            'account_nickname': self.account_nickname,
            'login_username': self.login_username,
            'success': self.success,
            'reservation_number': self.reservation_number,
            'selected_seat': self.selected_seat,
            'error_message': self.error_message,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'attempts': self.attempts,
            'duration_ms': self.duration_ms
        }


class MultiAccountReservationService:
    """
    여러 계정으로 동시에 예약 시도하는 서비스 (고도화 버전)

    Features:
    - Wave Attack: 계정별 시차(50ms) 발송
    - Burst Retry: 실패 시 50/100/200ms 즉시 재시도
    - Pre-fire: RTT 보상으로 정확한 시간에 서버 도달
    - Session Warmup: 예약 전 사전 로그인
    - Priority Seat Pool: 다중 좌석 우선순위 폴백
    """

    def __init__(self):
        self.results_lock = threading.Lock()
        self.advanced_service = AdvancedReservationService()

    def attempt_reservation_with_accounts(
        self,
        camping_site: CampingSite,
        target_date: str,
        product_codes: Optional[List[str]] = None,
        product_group_code: Optional[str] = None,
        reservation_time: Optional[str] = None,
        server_time_offset: float = 0
    ) -> Dict:
        """
        여러 계정으로 동시에 예약 시도

        Args:
            camping_site: 캠핑장 정보
            target_date: 예약 날짜 (YYYY-MM-DD)
            product_codes: 우선순위 좌석 코드 목록 (선택)
            product_group_code: 시설 그룹 코드 (선택, 기본값: 0004=파쇄석)
            reservation_time: 예약 시작 시간 (HH:MM) (선택)
            server_time_offset: 서버 시간 오프셋 (초)

        Returns:
            Dict: {
                'success': bool,
                'accounts_attempted': int,
                'successful_account': Dict or None,
                'all_results': List[Dict],
                'message': str
            }
        """
        logger.info(f"🚀 멀티 계정 예약 시작: {camping_site.name} - {target_date}")

        # 기본값 설정
        if product_codes is None:
            product_codes = []
        if product_group_code is None:
            product_group_code = "0004"  # 파쇄석 기본값

        # 예약 시간이 지정된 경우 해당 시간까지 대기
        if reservation_time:
            self._wait_until_reservation_time(reservation_time, server_time_offset)

        # 활성화된 계정 가져오기 (우선순위 순)
        active_accounts = CampingSiteAccount.query.filter_by(
            camping_site_id=camping_site.id,
            is_active=True
        ).order_by(CampingSiteAccount.priority).all()

        if not active_accounts:
            logger.warning(f"⚠️ 활성화된 계정이 없습니다: {camping_site.name}")
            return {
                'success': False,
                'accounts_attempted': 0,
                'successful_account': None,
                'all_results': [],
                'message': '활성화된 계정이 없습니다'
            }

        logger.info(f"📋 {len(active_accounts)}개의 활성 계정으로 동시 예약 시도")
        logger.info(f"   Product codes: {product_codes}")
        logger.info(f"   Product group code: {product_group_code}")

        # 결과 저장 리스트
        results = []
        threads = []

        # 각 계정마다 스레드 생성
        for account in active_accounts:
            result = AccountReservationResult(
                account_id=account.id,
                account_nickname=account.nickname or f"계정 {account.id}",
                login_username=account.login_username
            )
            results.append(result)

            thread = threading.Thread(
                target=self._attempt_single_account,
                args=(account, camping_site, target_date, product_codes, product_group_code, result),
                name=f"Account-{account.id}"
            )
            threads.append(thread)
            thread.start()
            logger.info(f"🔄 스레드 시작: {account.nickname or account.login_username} (우선순위: {account.priority})")

        # 모든 스레드가 종료될 때까지 대기
        for thread in threads:
            thread.join()

        logger.info(f"✅ 모든 스레드 종료 완료")

        # 성공한 계정들 찾기
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        if successful_results:
            logger.success(f"🎉 예약 성공: {len(successful_results)}개 계정")
            for success in successful_results:
                logger.success(f"  - {success.account_nickname}: {success.reservation_number}")

            return {
                'success': True,
                'accounts_attempted': len(active_accounts),
                'successful_count': len(successful_results),
                'failed_count': len(failed_results),
                'all_results': [r.to_dict() for r in results],
                'message': f'{len(successful_results)}개 계정 예약 성공, {len(failed_results)}개 실패'
            }
        else:
            logger.error(f"❌ 모든 계정 예약 실패: {len(failed_results)}개 계정")

            return {
                'success': False,
                'accounts_attempted': len(active_accounts),
                'successful_count': 0,
                'failed_count': len(failed_results),
                'all_results': [r.to_dict() for r in results],
                'message': f'모든 계정 예약 실패 ({len(failed_results)}개 시도)'
            }

    def _attempt_single_account(
        self,
        account: CampingSiteAccount,
        camping_site: CampingSite,
        target_date: str,
        product_codes: List[str],
        product_group_code: str,
        result: AccountReservationResult
    ):
        """
        단일 계정으로 예약 시도 (스레드 함수)

        Args:
            account: 계정 정보
            camping_site: 캠핑장 정보
            target_date: 예약 날짜 (YYYY-MM-DD)
            product_codes: 우선순위 좌석 코드 목록
            product_group_code: 시설 그룹 코드
            result: 결과 객체 (참조로 업데이트)
        """
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 예약 시도 시작: {account.nickname or account.login_username}")

        start_time = time.time()

        try:
            # 캠핑장 URL에서 shop_encode, shop_code 파싱
            shop_encode, shop_code = self._parse_camping_site_url(camping_site.url)

            # XTicket 스크래퍼 생성
            scraper = XTicketScraper(shop_encode, shop_code)

            # 로그인
            logger.info(f"[{thread_name}] 로그인 중...")
            login_success = scraper.login(account.login_username, account.login_password)

            if not login_success:
                with self.results_lock:
                    result.success = False
                    result.error_message = "로그인 실패"
                logger.error(f"[{thread_name}] ❌ 로그인 실패")
                return

            # 예약 시도
            logger.info(f"[{thread_name}] 예약 진행 중...")
            reservation_result = scraper.make_reservation(
                target_date=target_date,
                product_codes=product_codes,
                product_group_code=product_group_code,
                book_days=1
            )

            # 결과 업데이트
            with self.results_lock:
                result.duration_ms = (time.time() - start_time) * 1000
                result.attempts = 1

                if reservation_result.get('success'):
                    result.success = True
                    result.reservation_number = reservation_result.get('reservation_number')
                    result.selected_seat = reservation_result.get('selected_site')
                    result.completed_at = datetime.utcnow()
                    logger.success(f"[{thread_name}] ✅ 예약 성공: {result.reservation_number}")
                else:
                    result.success = False
                    result.error_message = reservation_result.get('error', '알 수 없는 오류')
                    logger.warning(f"[{thread_name}] ❌ 예약 실패: {result.error_message}")

            # 로그아웃
            scraper.logout()

        except Exception as e:
            with self.results_lock:
                result.success = False
                result.error_message = str(e)
                result.duration_ms = (time.time() - start_time) * 1000
                logger.error(f"[{thread_name}] ❌ 예외 발생: {e}")

        finally:
            logger.info(f"[{thread_name}] 스레드 종료")

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

        # shop_code는 기본값 사용 (추후 캠핑장 모델에 추가 권장)
        shop_code = "622830018001"  # 생림오토캠핑장 기본값

        if not shop_encode:
            # URL에서 직접 추출 시도
            match = re.search(r'shopEncode=([^&]+)', url)
            if match:
                shop_encode = match.group(1)

        return shop_encode, shop_code

    def _wait_until_reservation_time(self, reservation_time: str, server_time_offset: float = 0):
        """
        지정된 예약 시간까지 대기 (서버 시간 오프셋 적용)

        Args:
            reservation_time: 예약 시작 시간 (HH:MM)
            server_time_offset: 서버 시간 - 로컬 시간 (초 단위)
        """
        try:
            target_hour, target_minute = map(int, reservation_time.split(':'))

            logger.info(f"⏰ 예약 시간: {reservation_time}, 서버 시간 오프셋: {server_time_offset:.3f}초")

            while True:
                # 로컬 시간에 오프셋을 더해서 서버 시간 계산
                now_local = datetime.now()
                now_server = now_local + timedelta(seconds=server_time_offset)

                current_hour = now_server.hour
                current_minute = now_server.minute
                current_second = now_server.second

                # 목표 시간이 현재 시간보다 이전이면 다음 날로 간주
                if (current_hour > target_hour) or (current_hour == target_hour and current_minute >= target_minute):
                    logger.warning(f"⚠️ 예약 시간({reservation_time})이 이미 지났습니다. 즉시 시작합니다.")
                    logger.info(f"현재 서버 시간: {now_server.strftime('%H:%M:%S')}")
                    break

                # 남은 시간 계산 (서버 시간 기준)
                remaining_seconds = (target_hour - current_hour) * 3600 + \
                                  (target_minute - current_minute) * 60 - current_second

                if remaining_seconds <= 0:
                    logger.info(f"⏰ 예약 시간 도달! 시작합니다.")
                    logger.info(f"현재 서버 시간: {now_server.strftime('%H:%M:%S')}")
                    break

                # 10초 이상 남았으면 상태 로그 출력
                if remaining_seconds > 10:
                    logger.info(f"⏳ 예약 시간({reservation_time})까지 {remaining_seconds}초 대기 중... (서버 시간: {now_server.strftime('%H:%M:%S')})")
                    time.sleep(min(10, remaining_seconds))
                else:
                    # 마지막 10초는 정밀하게 대기
                    logger.info(f"⏳ {remaining_seconds}초 후 시작... (서버 시간: {now_server.strftime('%H:%M:%S')})")
                    time.sleep(remaining_seconds)
                    break

        except ValueError as e:
            logger.error(f"❌ 잘못된 시간 형식: {reservation_time}. 형식: HH:MM")
            logger.info(f"즉시 시작합니다.")

    def attempt_reservation_sequential(
        self,
        camping_site: CampingSite,
        target_date: str,
        product_codes: Optional[List[str]] = None,
        product_group_code: Optional[str] = None
    ) -> Dict:
        """
        여러 계정으로 순차적으로 예약 시도 (비교용)
        첫 번째 성공 시 중단

        Args:
            camping_site: 캠핑장 정보
            target_date: 예약 날짜 (YYYY-MM-DD)
            product_codes: 우선순위 좌석 코드 목록 (선택)
            product_group_code: 시설 그룹 코드 (선택, 기본값: 0004=파쇄석)

        Returns:
            Dict: 예약 결과
        """
        logger.info(f"🔄 순차 예약 시작: {camping_site.name} - {target_date}")

        # 기본값 설정
        if product_codes is None:
            product_codes = []
        if product_group_code is None:
            product_group_code = "0004"

        active_accounts = CampingSiteAccount.query.filter_by(
            camping_site_id=camping_site.id,
            is_active=True
        ).order_by(CampingSiteAccount.priority).all()

        if not active_accounts:
            return {
                'success': False,
                'accounts_attempted': 0,
                'successful_account': None,
                'message': '활성화된 계정이 없습니다'
            }

        for account in active_accounts:
            logger.info(f"🔄 시도 중: {account.nickname or account.login_username}")

            result = AccountReservationResult(
                account_id=account.id,
                account_nickname=account.nickname or f"계정 {account.id}",
                login_username=account.login_username
            )

            self._attempt_single_account(
                account, camping_site, target_date, product_codes, product_group_code, result
            )

            if result.success:
                logger.success(f"✅ 순차 예약 성공: {result.account_nickname}")
                return {
                    'success': True,
                    'accounts_attempted': active_accounts.index(account) + 1,
                    'successful_account': result.to_dict(),
                    'message': f'{result.account_nickname} 계정으로 예약 성공'
                }

        logger.error(f"❌ 모든 계정 순차 예약 실패")
        return {
            'success': False,
            'accounts_attempted': len(active_accounts),
            'successful_account': None,
            'message': '모든 계정 예약 실패'
        }

    def attempt_advanced_reservation(
        self,
        schedule_id: int,
        camping_site: CampingSite,
        target_date: str,
        seats: List[CampingSiteSeat],
        accounts: List[CampingSiteAccount],
        wave_interval_ms: int = 50,
        burst_retry_count: int = 3,
        pre_fire_ms: int = 0,
        reservation_time: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict:
        """
        고급 예약 실행 (Wave Attack + Burst Retry + Pre-fire + Priority Seat Pool)

        Session Warmup이 완료된 상태에서 호출해야 합니다.

        Args:
            schedule_id: 스케줄 ID (세션 워밍업 참조용)
            camping_site: 캠핑장 정보
            target_date: 예약 날짜 (YYYY-MM-DD)
            seats: 우선순위 순 좌석 목록
            accounts: 사용할 계정 목록
            wave_interval_ms: Wave Attack 간격 (ms)
            burst_retry_count: Burst Retry 횟수
            pre_fire_ms: Pre-fire 시간 (ms)
            reservation_time: 예약 시작 시간 (HH:MM, 선택)

        Returns:
            예약 결과
        """
        logger.info(f"🚀 고급 예약 시작: {camping_site.name}")
        logger.info(f"   Target date: {target_date}")
        logger.info(f"   Seats: {len(seats)}, Accounts: {len(accounts)}")
        logger.info(f"   Wave interval: {wave_interval_ms}ms, Burst retries: {burst_retry_count}")
        logger.info(f"   Pre-fire: {pre_fire_ms}ms")

        # 세션 워밍업에서 준비된 스크래퍼 가져오기
        scrapers = session_warmup_service.get_ready_scrapers(schedule_id)

        if not scrapers:
            logger.error("❌ 준비된 스크래퍼가 없습니다. 세션 워밍업이 실패했을 수 있습니다.")
            return {
                'success': False,
                'message': '세션 워밍업 실패 - 준비된 스크래퍼 없음',
                'all_results': []
            }

        logger.info(f"✅ {len(scrapers)}개의 준비된 스크래퍼 확인")

        # 시간 동기화 객체 가져오기
        time_sync = session_warmup_service.get_time_sync(schedule_id)

        # 예약 시간까지 대기 (Pre-fire 적용)
        if reservation_time:
            self._wait_until_with_prefire(reservation_time, time_sync, pre_fire_ms)

        # 상품 그룹 코드 결정
        product_group_code = seats[0].product_group_code if seats else "0004"

        # Wave Attack 실행
        result = self.advanced_service.execute_reservation(
            scrapers=scrapers,
            accounts=accounts,
            target_date=target_date,
            seats=seats,
            product_group_code=product_group_code,
            wave_interval_ms=wave_interval_ms,
            burst_retry_count=burst_retry_count,
            dry_run=dry_run
        )

        return result

    def _wait_until_with_prefire(
        self,
        reservation_time: str,
        time_sync: Optional[PreciseTimeSync],
        pre_fire_ms: int
    ):
        """
        Pre-fire를 적용한 정밀 대기

        Args:
            reservation_time: 예약 시작 시간 (HH:MM)
            time_sync: 시간 동기화 객체
            pre_fire_ms: Pre-fire 시간 (ms)
        """
        try:
            target_hour, target_minute = map(int, reservation_time.split(':'))

            # 서버 시간 오프셋
            server_offset = time_sync.get_offset() if time_sync else 0
            rtt = time_sync.get_rtt() if time_sync else 100

            # Pre-fire 계산: 지정된 값 또는 RTT/2
            actual_pre_fire_ms = pre_fire_ms if pre_fire_ms > 0 else (rtt / 2)

            logger.info(f"⏰ 예약 시간: {reservation_time}")
            logger.info(f"   서버 오프셋: {server_offset*1000:.1f}ms")
            logger.info(f"   RTT: {rtt:.1f}ms")
            logger.info(f"   Pre-fire: {actual_pre_fire_ms:.1f}ms")

            while True:
                # 서버 시간 기준 현재 시간
                now_local = datetime.now()
                now_server = now_local + timedelta(seconds=server_offset)

                current_hour = now_server.hour
                current_minute = now_server.minute
                current_second = now_server.second
                current_ms = now_server.microsecond / 1000

                # 목표 시간이 이미 지났으면 즉시 시작
                if (current_hour > target_hour) or \
                   (current_hour == target_hour and current_minute >= target_minute):
                    logger.warning(f"⚠️ 예약 시간이 이미 지났습니다. 즉시 시작합니다.")
                    break

                # 남은 시간 계산 (밀리초 단위)
                remaining_ms = ((target_hour - current_hour) * 3600 +
                               (target_minute - current_minute) * 60 -
                               current_second) * 1000 - current_ms

                # Pre-fire 적용
                adjusted_remaining = remaining_ms - actual_pre_fire_ms

                if adjusted_remaining <= 0:
                    logger.info(f"🎯 Pre-fire 시점 도달! 발사합니다.")
                    logger.info(f"   서버 시간: {now_server.strftime('%H:%M:%S.%f')[:-3]}")
                    break

                # 대기 전략
                if adjusted_remaining > 10000:  # 10초 이상
                    sleep_time = (adjusted_remaining - 10000) / 1000
                    logger.debug(f"⏳ {adjusted_remaining/1000:.1f}초 남음, {sleep_time:.1f}초 대기")
                    time.sleep(min(5, sleep_time))
                elif adjusted_remaining > 1000:  # 1~10초
                    time.sleep(0.1)  # 100ms
                elif adjusted_remaining > 100:  # 100ms~1초
                    time.sleep(0.01)  # 10ms
                else:
                    # 100ms 이하: busy-wait
                    pass

        except ValueError as e:
            logger.error(f"❌ 잘못된 시간 형식: {reservation_time}")
            logger.info(f"즉시 시작합니다.")

    def warmup_sessions(
        self,
        schedule_id: int,
        camping_site: CampingSite,
        accounts: List[CampingSiteAccount],
        execute_at: datetime
    ) -> Dict:
        """
        세션 워밍업 시작

        Args:
            schedule_id: 스케줄 ID
            camping_site: 캠핑장 정보
            accounts: 로그인할 계정 목록
            execute_at: 예약 실행 시간

        Returns:
            워밍업 상태
        """
        sessions = session_warmup_service.warmup_for_schedule(
            schedule_id=schedule_id,
            camping_site=camping_site,
            accounts=accounts,
            execute_at=execute_at
        )

        return session_warmup_service.get_session_status(schedule_id)

    def cleanup_sessions(self, schedule_id: int):
        """세션 정리"""
        session_warmup_service.stop_warmup(schedule_id)
