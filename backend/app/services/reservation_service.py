"""예약 서비스"""
import os
from datetime import datetime
from loguru import logger

from app import db
from app.models.database import CampingSite, Reservation
from app.scrapers.gocamp_scraper import GoCampScraper
from app.scrapers.naver_scraper import NaverScraper
from app.scrapers.xticket_scraper import XTicketScraper
from app.notifications.telegram_notifier import TelegramNotifier


class ReservationService:
    """예약 관리 서비스"""

    def __init__(self):
        self.scrapers = {
            'gocamp': GoCampScraper(),
            'naver': NaverScraper(),
            'xticket': self._create_xticket_scraper()
        }
        self.notifier = TelegramNotifier()

    def _create_xticket_scraper(self):
        """XTicket 스크래퍼 생성 (환경변수 기반)"""
        shop_encode = os.getenv('XTICKET_SHOP_ENCODE')
        shop_code = os.getenv('XTICKET_SHOP_CODE')

        if not shop_encode or not shop_code:
            logger.warning("XTicket credentials not configured")
            return None

        # 환경변수에서 재시도 설정 가져오기
        max_retries = int(os.getenv('MAX_RETRIES', 3))
        timeout = int(os.getenv('REQUEST_TIMEOUT', 30))

        return XTicketScraper(
            shop_encode=shop_encode,
            shop_code=shop_code,
            max_retries=max_retries,
            timeout=timeout
        )

    def create_reservation(self, camping_site_id: int, check_in_date: str,
                          check_out_date: str, user_info: dict):
        """예약 생성 및 실행"""
        camping_site = CampingSite.query.get_or_404(camping_site_id)
        scraper = self.scrapers.get(camping_site.site_type)

        if not scraper:
            raise ValueError(f"No scraper found for site type: {camping_site.site_type}")

        # 예약 레코드 생성
        reservation = Reservation(
            camping_site_id=camping_site_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            status='processing'
        )

        db.session.add(reservation)
        db.session.commit()

        logger.info(f"Created reservation {reservation.id} for {camping_site.name}")

        try:
            # 예약 실행
            result = scraper.make_reservation(
                camping_site.url,
                check_in_date,
                check_out_date,
                user_info
            )

            if result['success']:
                reservation.status = 'reserved'
                reservation.reservation_number = result.get('reservation_number')
                logger.info(f"Reservation {reservation.id} successful")

                # 성공 알림
                self.notifier.send_reservation_success(
                    camping_site.name,
                    check_in_date,
                    result.get('reservation_number')
                )
            else:
                reservation.status = 'failed'
                reservation.error_message = result.get('error')
                logger.error(f"Reservation {reservation.id} failed: {result.get('error')}")

                # 실패 알림
                self.notifier.send_reservation_failure(
                    camping_site.name,
                    check_in_date,
                    result.get('error')
                )

        except Exception as e:
            reservation.status = 'failed'
            reservation.error_message = str(e)
            logger.error(f"Exception during reservation {reservation.id}: {e}")

            # 에러 알림
            self.notifier.send_error_notification(str(e))

        finally:
            reservation.updated_at = datetime.utcnow()
            db.session.commit()

        return reservation.to_dict()
