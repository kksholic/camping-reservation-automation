"""모니터링 서비스"""
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from app import db
from app.models.database import MonitoringTarget, Reservation, AppSettings
from app.scrapers.gocamp_scraper import GoCampScraper
from app.scrapers.naver_scraper import NaverScraper
from app.scrapers.xticket_scraper import XTicketScraper
from app.notifications.telegram_notifier import TelegramNotifier


class MonitorService:
    """캠핑 예약 모니터링 서비스"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.scrapers = {
            'gocamp': GoCampScraper(),
            'naver': NaverScraper(),
            'xticket': self._create_xticket_scraper()
        }
        self.notifier = self._create_notifier()

    def _create_notifier(self):
        """텔레그램 알림 생성 - DB 설정 우선 사용"""
        try:
            settings = AppSettings.query.first()
            if settings and settings.telegram_bot_token and settings.telegram_chat_id:
                logger.info("Using Telegram settings from database")
                return TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
        except Exception as e:
            logger.warning(f"Failed to load Telegram settings from DB: {e}")

        logger.info("Using Telegram settings from environment")
        return TelegramNotifier()  # 환경 변수 fallback

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

    def start(self):
        """모니터링 시작"""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return

        logger.info("Starting monitoring service")

        # 스케줄러에 작업 추가 (60초마다 실행)
        self.scheduler.add_job(
            self.check_all_targets,
            'interval',
            seconds=60,
            id='monitoring_job'
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("Monitoring service started")

    def stop(self):
        """모니터링 중지"""
        if not self.is_running:
            logger.warning("Monitoring is not running")
            return

        logger.info("Stopping monitoring service")
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Monitoring service stopped")

    def check_all_targets(self):
        """모든 모니터링 타겟 확인"""
        logger.info("Checking all monitoring targets")

        targets = MonitoringTarget.query.filter_by(is_active=True).all()

        for target in targets:
            try:
                self.check_target(target)
            except Exception as e:
                logger.error(f"Error checking target {target.id}: {e}")

    def check_target(self, target: MonitoringTarget):
        """개별 타겟 확인"""
        camping_site = target.camping_site
        scraper = self.scrapers.get(camping_site.site_type)

        if not scraper:
            logger.error(f"No scraper found for site type: {camping_site.site_type}")
            return

        logger.info(f"Checking target {target.id} for {camping_site.name}")

        # 예약 가능 여부 확인
        is_available = scraper.check_availability(
            camping_site.url,
            target.target_date
        )

        # 상태 업데이트
        previous_status = target.last_status
        target.last_status = 'available' if is_available else 'unavailable'
        target.last_checked = datetime.utcnow()

        # 예약 가능으로 변경된 경우
        if is_available and previous_status == 'unavailable':
            logger.info(f"Target {target.id} is now available!")

            # 텔레그램 알림
            if not target.notification_sent:
                self.notifier.send_availability_notification(
                    camping_site.name,
                    target.target_date
                )
                target.notification_sent = True

            # 예약 레코드 업데이트
            reservation = Reservation.query.filter_by(
                camping_site_id=camping_site.id,
                check_in_date=target.target_date
            ).first()

            if reservation:
                reservation.status = 'available'
                reservation.updated_at = datetime.utcnow()

        db.session.commit()

    def schedule_at_specific_time(self, hour: int, minute: int, second: int = 0,
                                  job_id: str = None):
        """
        특정 시간에 예약 실행 스케줄 등록

        Args:
            hour: 시 (0-23)
            minute: 분 (0-59)
            second: 초 (0-59)
            job_id: 작업 ID (선택사항)

        Returns:
            str: 생성된 작업 ID
        """
        from apscheduler.triggers.cron import CronTrigger

        if not self.scheduler.running:
            self.scheduler.start()
            self.is_running = True

        if job_id is None:
            job_id = f'scheduled_reservation_{hour:02d}{minute:02d}{second:02d}'

        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            second=second
        )

        self.scheduler.add_job(
            self.execute_scheduled_reservations,
            trigger=trigger,
            id=job_id,
            replace_existing=True
        )

        logger.info(f"Scheduled job {job_id} at {hour:02d}:{minute:02d}:{second:02d}")
        return job_id

    def execute_scheduled_reservations(self):
        """스케줄된 예약 실행"""
        logger.info("Executing scheduled reservations")

        # 활성화된 모든 모니터링 타겟 확인 및 예약 시도
        targets = MonitoringTarget.query.filter_by(is_active=True).all()

        for target in targets:
            try:
                camping_site = target.camping_site
                scraper = self.scrapers.get(camping_site.site_type)

                if not scraper:
                    logger.error(f"No scraper for site type: {camping_site.site_type}")
                    continue

                # 예약 가능 여부 확인
                is_available = scraper.check_availability(
                    camping_site.url,
                    target.target_date
                )

                if is_available:
                    logger.info(f"Attempting reservation for {camping_site.name}")
                    # 예약 서비스를 통한 예약 실행은 별도 로직 필요
                    # 여기서는 알림만 전송
                    self.notifier.send_availability_notification(
                        camping_site.name,
                        target.target_date
                    )

            except Exception as e:
                logger.error(f"Error executing scheduled reservation for target {target.id}: {e}")

    def remove_scheduled_job(self, job_id: str):
        """스케줄된 작업 제거"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed scheduled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False

    def list_scheduled_jobs(self):
        """스케줄된 작업 목록 조회"""
        if not self.scheduler.running:
            return []

        jobs = self.scheduler.get_jobs()
        return [{
            'id': job.id,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        } for job in jobs]

    def get_status(self):
        """모니터링 상태 조회"""
        return {
            'is_running': self.is_running,
            'active_targets': MonitoringTarget.query.filter_by(is_active=True).count(),
            'scheduler_jobs': len(self.scheduler.get_jobs()) if self.is_running else 0,
            'scheduled_jobs': self.list_scheduled_jobs()
        }
