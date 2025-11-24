"""
멀티 계정 동시 예약 서비스
여러 계정으로 동시에 예약을 시도하는 서비스
"""
import threading
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from app.models.database import CampingSite, CampingSiteAccount, Reservation
from app import db
from app.scrapers.xticket_scraper import XTicketScraper


class AccountReservationResult:
    """계정별 예약 결과"""
    def __init__(self, account_id: int, account_nickname: str, login_username: str):
        self.account_id = account_id
        self.account_nickname = account_nickname
        self.login_username = login_username
        self.success = False
        self.reservation_number = None
        self.error_message = None
        self.completed_at = None

    def to_dict(self):
        return {
            'account_id': self.account_id,
            'account_nickname': self.account_nickname,
            'login_username': self.login_username,
            'success': self.success,
            'reservation_number': self.reservation_number,
            'error_message': self.error_message,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class MultiAccountReservationService:
    """여러 계정으로 동시에 예약 시도하는 서비스"""

    def __init__(self):
        self.results_lock = threading.Lock()

    def attempt_reservation_with_accounts(
        self,
        camping_site: CampingSite,
        target_date: str,
        site_name: Optional[str] = None,
        zone_code: Optional[str] = None
    ) -> Dict:
        """
        여러 계정으로 동시에 예약 시도

        Args:
            camping_site: 캠핑장 정보
            target_date: 예약 날짜 (YYYY-MM-DD)
            site_name: 사이트 이름 (선택)
            zone_code: 구역 코드 (선택)

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
                args=(account, camping_site, target_date, site_name, zone_code, result),
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
        site_name: Optional[str],
        zone_code: Optional[str],
        result: AccountReservationResult
    ):
        """
        단일 계정으로 예약 시도 (스레드 함수)

        Args:
            account: 계정 정보
            camping_site: 캠핑장 정보
            target_date: 예약 날짜
            site_name: 사이트 이름
            zone_code: 구역 코드
            result: 결과 객체 (참조로 업데이트)
        """
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 예약 시도 시작: {account.nickname or account.login_username}")

        try:
            # XTicket 스크래퍼 생성
            scraper = XTicketScraper(camping_site.url)

            # 예약 시도
            logger.info(f"[{thread_name}] 예약 진행 중...")
            reservation_result = scraper.make_reservation(
                url=camping_site.url,
                check_in=target_date,
                check_out=target_date,  # 당일 예약
                login_username=account.login_username,
                login_password=account.login_password,
                booker_name=account.booker_name,
                booker_phone=account.booker_phone,
                booker_car_number=account.booker_car_number,
                site_name=site_name,
                zone_code=zone_code
            )

            # 결과 업데이트
            with self.results_lock:
                if reservation_result['success']:
                    result.success = True
                    result.reservation_number = reservation_result.get('reservation_number')
                    result.completed_at = datetime.utcnow()
                    logger.success(f"[{thread_name}] ✅ 예약 성공: {result.reservation_number}")
                else:
                    result.success = False
                    result.error_message = reservation_result.get('message', '알 수 없는 오류')
                    logger.warning(f"[{thread_name}] ❌ 예약 실패: {result.error_message}")

        except Exception as e:
            with self.results_lock:
                result.success = False
                result.error_message = str(e)
                logger.error(f"[{thread_name}] ❌ 예외 발생: {e}")

        finally:
            logger.info(f"[{thread_name}] 스레드 종료")

    def attempt_reservation_sequential(
        self,
        camping_site: CampingSite,
        target_date: str,
        site_name: Optional[str] = None,
        zone_code: Optional[str] = None
    ) -> Dict:
        """
        여러 계정으로 순차적으로 예약 시도 (비교용)
        첫 번째 성공 시 중단

        Returns:
            Dict: 예약 결과
        """
        logger.info(f"🔄 순차 예약 시작: {camping_site.name} - {target_date}")

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
                account, camping_site, target_date, site_name, zone_code, result
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
