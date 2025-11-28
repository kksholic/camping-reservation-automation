"""
Wave Attack + Burst Retry 서비스

여러 계정으로 시차를 두고 동시 예약을 시도하고,
실패 시 밀리초 단위로 즉시 재시도하는 고급 예약 전략을 구현합니다.
"""
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from app.models.database import CampingSiteAccount, CampingSiteSeat
from app.scrapers.xticket_scraper import XTicketScraper


class ReservationErrorType(Enum):
    """예약 실패 유형"""
    SUCCESS = "success"
    CAPTCHA_ERROR = "captcha_error"  # CAPTCHA 오류 - 재시도 가능
    NO_SEAT = "no_seat"  # 좌석 없음 - 다음 좌석으로
    NETWORK_ERROR = "network_error"  # 네트워크 오류 - 재시도 가능
    AUTH_ERROR = "auth_error"  # 인증 오류 - 재로그인 필요
    UNKNOWN_ERROR = "unknown_error"  # 알 수 없는 오류


@dataclass
class BurstRetryConfig:
    """Burst Retry 설정"""
    max_retries: int = 3
    intervals_ms: List[int] = field(default_factory=lambda: [50, 100, 200])
    retry_on: List[ReservationErrorType] = field(default_factory=lambda: [
        ReservationErrorType.CAPTCHA_ERROR,
        ReservationErrorType.NETWORK_ERROR
    ])


@dataclass
class WaveAttackConfig:
    """Wave Attack 설정"""
    interval_ms: int = 50  # 계정 간 시작 간격 (ms)
    stop_on_success: bool = True  # 첫 성공 시 나머지 중단
    max_parallel: int = 10  # 최대 동시 실행 계정 수


@dataclass
class AccountResult:
    """계정별 예약 결과"""
    account_id: int
    account_nickname: str
    success: bool = False
    reservation_number: Optional[str] = None
    selected_seat: Optional[str] = None
    error_type: ReservationErrorType = ReservationErrorType.UNKNOWN_ERROR
    error_message: Optional[str] = None
    attempts: int = 0
    duration_ms: float = 0
    completed_at: Optional[datetime] = None

    def to_dict(self):
        return {
            'account_id': self.account_id,
            'account_nickname': self.account_nickname,
            'success': self.success,
            'reservation_number': self.reservation_number,
            'selected_seat': self.selected_seat,
            'error_type': self.error_type.value,
            'error_message': self.error_message,
            'attempts': self.attempts,
            'duration_ms': self.duration_ms,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class BurstRetry:
    """
    Burst Retry: 밀리초 단위 즉시 재시도

    예약 실패 시 50ms, 100ms, 200ms 간격으로 빠르게 재시도
    """

    def __init__(self, config: BurstRetryConfig = None):
        self.config = config or BurstRetryConfig()

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Dict:
        """
        재시도 로직 적용하여 함수 실행

        Args:
            func: 실행할 함수
            *args, **kwargs: 함수 인자

        Returns:
            실행 결과
        """
        last_result = None
        total_attempts = 0

        for attempt in range(self.config.max_retries + 1):
            total_attempts += 1

            try:
                result = func(*args, **kwargs)
                last_result = result

                # 성공
                if result.get('success'):
                    logger.info(f"✅ Success on attempt {total_attempts}")
                    return {
                        **result,
                        'attempts': total_attempts,
                        'error_type': ReservationErrorType.SUCCESS
                    }

                # 실패 유형 판별
                error_type = self._classify_error(result)
                result['error_type'] = error_type

                # 좌석 없음은 재시도 무의미
                if error_type == ReservationErrorType.NO_SEAT:
                    logger.warning(f"⚠️ No seat available, stopping retry")
                    return {
                        **result,
                        'attempts': total_attempts
                    }

                # 재시도 불가능한 오류
                if error_type not in self.config.retry_on:
                    logger.warning(f"⚠️ Error type {error_type.value} not retryable")
                    return {
                        **result,
                        'attempts': total_attempts
                    }

                # 재시도 대기
                if attempt < self.config.max_retries:
                    wait_ms = self.config.intervals_ms[min(attempt, len(self.config.intervals_ms) - 1)]
                    logger.debug(f"🔄 Retry in {wait_ms}ms (attempt {attempt + 1})")
                    time.sleep(wait_ms / 1000)

            except Exception as e:
                logger.error(f"❌ Exception on attempt {total_attempts}: {e}")
                last_result = {
                    'success': False,
                    'error': str(e),
                    'error_type': ReservationErrorType.UNKNOWN_ERROR
                }

                if attempt < self.config.max_retries:
                    wait_ms = self.config.intervals_ms[min(attempt, len(self.config.intervals_ms) - 1)]
                    time.sleep(wait_ms / 1000)

        return {
            **(last_result or {}),
            'attempts': total_attempts
        }

    def _classify_error(self, result: Dict) -> ReservationErrorType:
        """오류 유형 분류"""
        error_msg = result.get('error', '').lower()
        message = result.get('message', '').lower()

        combined = f"{error_msg} {message}"

        if 'captcha' in combined or '자동입력' in combined or '인증코드' in combined:
            return ReservationErrorType.CAPTCHA_ERROR
        elif '예약' in combined and ('없' in combined or '마감' in combined or '불가' in combined):
            return ReservationErrorType.NO_SEAT
        elif '로그인' in combined or '인증' in combined or 'login' in combined:
            return ReservationErrorType.AUTH_ERROR
        elif 'timeout' in combined or 'connection' in combined or '네트워크' in combined:
            return ReservationErrorType.NETWORK_ERROR
        else:
            return ReservationErrorType.UNKNOWN_ERROR


class WaveAttackService:
    """
    Wave Attack: 시차를 둔 동시 예약 요청

    여러 계정이 50ms 간격으로 순차 시작하여 서버의 부하 분산을 피하면서
    동시에 예약을 시도
    """

    def __init__(self, config: WaveAttackConfig = None, burst_config: BurstRetryConfig = None):
        self.config = config or WaveAttackConfig()
        self.burst_retry = BurstRetry(burst_config)
        self._stop_event = threading.Event()
        self._success_event = threading.Event()
        self._results_lock = threading.Lock()
        self._results: List[AccountResult] = []

    def execute_wave_attack(
        self,
        scrapers: Dict[int, XTicketScraper],  # account_id -> scraper
        accounts: List[CampingSiteAccount],
        target_date: str,
        seat_priority: List[CampingSiteSeat],  # 우선순위 순 좌석 목록
        product_group_code: str = "0004",
        dry_run: bool = False
    ) -> Dict:
        """
        Wave Attack 실행

        Args:
            scrapers: 계정별 로그인된 스크래퍼 (세션 워밍업 완료 상태)
            accounts: 예약 시도할 계정 목록 (우선순위 순)
            target_date: 예약 날짜 (YYYY-MM-DD)
            seat_priority: 우선순위 순 좌석 목록
            product_group_code: 시설 그룹 코드

        Returns:
            {
                'success': bool,
                'total_accounts': int,
                'successful_accounts': List[AccountResult],
                'failed_accounts': List[AccountResult],
                'first_success': AccountResult or None,
                'total_duration_ms': float
            }
        """
        logger.info(f"🌊 Wave Attack 시작: {len(accounts)}개 계정, {len(seat_priority)}개 좌석")

        # 초기화
        self._stop_event.clear()
        self._success_event.clear()
        self._results = []

        start_time = time.perf_counter()
        threads = []

        # 좌석 코드 목록 생성
        product_codes = [seat.product_code for seat in seat_priority]

        # 계정별 스레드 생성 (시차 적용)
        for idx, account in enumerate(accounts[:self.config.max_parallel]):
            if account.id not in scrapers:
                logger.warning(f"⚠️ Scraper not found for account {account.id}")
                continue

            scraper = scrapers[account.id]

            # Wave 간격 계산
            delay_ms = idx * self.config.interval_ms

            thread = threading.Thread(
                target=self._execute_single_account,
                args=(account, scraper, target_date, product_codes, product_group_code, delay_ms),
                name=f"Wave-{account.id}"
            )
            threads.append(thread)

        # 모든 스레드 시작 (거의 동시에)
        for thread in threads:
            thread.start()

        # 완료 대기
        for thread in threads:
            thread.join(timeout=60)  # 최대 60초 대기

        end_time = time.perf_counter()
        total_duration_ms = (end_time - start_time) * 1000

        # 결과 집계
        successful = [r for r in self._results if r.success]
        failed = [r for r in self._results if not r.success]

        logger.info(f"🏁 Wave Attack 완료: 성공 {len(successful)}, 실패 {len(failed)}, "
                   f"소요시간 {total_duration_ms:.0f}ms")

        return {
            'success': len(successful) > 0,
            'total_accounts': len(accounts),
            'successful_count': len(successful),
            'failed_count': len(failed),
            'successful_accounts': [r.to_dict() for r in successful],
            'failed_accounts': [r.to_dict() for r in failed],
            'first_success': successful[0].to_dict() if successful else None,
            'all_results': [r.to_dict() for r in self._results],
            'total_duration_ms': total_duration_ms
        }

    def _execute_single_account(
        self,
        account: CampingSiteAccount,
        scraper: XTicketScraper,
        target_date: str,
        product_codes: List[str],
        product_group_code: str,
        delay_ms: int
    ):
        """단일 계정 예약 실행 (스레드 함수)"""
        thread_name = threading.current_thread().name
        result = AccountResult(
            account_id=account.id,
            account_nickname=account.nickname or account.login_username
        )

        try:
            # Wave 지연
            if delay_ms > 0:
                logger.debug(f"[{thread_name}] Waiting {delay_ms}ms...")
                time.sleep(delay_ms / 1000)

            # 이미 다른 계정이 성공했으면 중단
            if self.config.stop_on_success and self._success_event.is_set():
                logger.info(f"[{thread_name}] Skipping - another account succeeded")
                result.error_message = "Skipped - another account succeeded"
                with self._results_lock:
                    self._results.append(result)
                return

            start_time = time.perf_counter()

            # Burst Retry 적용 예약 시도
            reservation_result = self.burst_retry.execute_with_retry(
                scraper.make_reservation,
                target_date=target_date,
                product_codes=product_codes,
                product_group_code=product_group_code,
                dry_run=dry_run
            )

            end_time = time.perf_counter()
            result.duration_ms = (end_time - start_time) * 1000
            result.attempts = reservation_result.get('attempts', 1)

            if reservation_result.get('success'):
                result.success = True
                result.reservation_number = reservation_result.get('reservation_number')
                result.selected_seat = reservation_result.get('selected_site')
                result.error_type = ReservationErrorType.SUCCESS
                result.completed_at = datetime.utcnow()

                # 성공 이벤트 설정
                self._success_event.set()

                logger.success(f"[{thread_name}] ✅ 예약 성공: {result.reservation_number}")
            else:
                result.success = False
                result.error_type = reservation_result.get('error_type', ReservationErrorType.UNKNOWN_ERROR)
                result.error_message = reservation_result.get('error') or reservation_result.get('message')

                logger.warning(f"[{thread_name}] ❌ 예약 실패: {result.error_message}")

        except Exception as e:
            result.success = False
            result.error_type = ReservationErrorType.UNKNOWN_ERROR
            result.error_message = str(e)
            logger.error(f"[{thread_name}] ❌ 예외 발생: {e}")

        finally:
            with self._results_lock:
                self._results.append(result)

    def stop(self):
        """Wave Attack 중단"""
        logger.info("🛑 Wave Attack 중단 요청")
        self._stop_event.set()


class AdvancedReservationService:
    """
    고급 예약 서비스

    Pre-fire + Wave Attack + Burst Retry + Priority Seat Pool을 통합한 예약 서비스
    """

    def __init__(self):
        self.wave_attack = None

    def execute_reservation(
        self,
        scrapers: Dict[int, XTicketScraper],
        accounts: List[CampingSiteAccount],
        target_date: str,
        seats: List[CampingSiteSeat],
        product_group_code: str = "0004",
        wave_interval_ms: int = 50,
        burst_retry_count: int = 3,
        dry_run: bool = False
    ) -> Dict:
        """
        고급 예약 실행

        Args:
            scrapers: 로그인된 스크래퍼 딕셔너리
            accounts: 계정 목록
            target_date: 예약 날짜
            seats: 우선순위 좌석 목록
            product_group_code: 시설 그룹 코드
            wave_interval_ms: Wave 간격
            burst_retry_count: Burst 재시도 횟수

        Returns:
            예약 결과
        """
        # 설정 구성
        wave_config = WaveAttackConfig(
            interval_ms=wave_interval_ms,
            stop_on_success=True
        )

        burst_config = BurstRetryConfig(
            max_retries=burst_retry_count,
            intervals_ms=[50, 100, 200]
        )

        # Wave Attack 서비스 생성
        self.wave_attack = WaveAttackService(wave_config, burst_config)

        # 실행
        return self.wave_attack.execute_wave_attack(
            scrapers=scrapers,
            accounts=accounts,
            target_date=target_date,
            seat_priority=seats,
            product_group_code=product_group_code,
            dry_run=dry_run
        )

    def stop(self):
        """예약 중단"""
        if self.wave_attack:
            self.wave_attack.stop()
