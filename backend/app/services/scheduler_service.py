"""
스케줄 예약 서비스 - APScheduler 기반 자동 예약 실행 (고도화 버전)

- Session Warmup: 예약 5분 전 사전 로그인
- Pre-fire: RTT 보상 선행 발송
- Wave Attack: 계정별 시차 발송
- Burst Retry: ms 단위 즉시 재시도
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime, timedelta
from loguru import logger
import os


class SchedulerService:
    """예약 스케줄러 서비스"""

    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._scheduler is None:
            self._init_scheduler()

    def _init_scheduler(self):
        """스케줄러 초기화"""
        # 데이터베이스 경로
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'scheduler_jobs.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        jobstores = {
            'default': SQLAlchemyJobStore(url=f'sqlite:///{db_path}')
        }

        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 60  # 1분 내 실행 실패해도 실행
        }

        self._scheduler = BackgroundScheduler(
            jobstores=jobstores,
            job_defaults=job_defaults,
            timezone='Asia/Seoul'
        )

        logger.info("Scheduler service initialized")

    def start(self):
        """스케줄러 시작"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """스케줄러 종료"""
        if self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def add_reservation_job(self, schedule_id: int, execute_at: datetime,
                            warmup_minutes: int = 5):
        """예약 작업 추가 (워밍업 포함)

        Args:
            schedule_id: ReservationSchedule ID
            execute_at: 실행 시간
            warmup_minutes: 워밍업 시작 시간 (분 전, 기본 5분)

        Returns:
            (job_id, warmup_job_id): APScheduler job IDs
        """
        job_id = f"reservation_{schedule_id}"
        warmup_job_id = f"warmup_{schedule_id}"

        # 기존 job이 있으면 제거
        self.remove_job(job_id)
        self.remove_job(warmup_job_id)

        # 워밍업 시작 시간 계산
        warmup_at = execute_at - timedelta(minutes=warmup_minutes)

        # 현재 시간 확인
        now = datetime.now()

        # 워밍업 작업 추가 (아직 시간이 안 지났으면)
        if warmup_at > now:
            warmup_job = self._scheduler.add_job(
                func=execute_session_warmup,
                trigger=DateTrigger(run_date=warmup_at),
                args=[schedule_id],
                id=warmup_job_id,
                name=f"Session Warmup #{schedule_id}",
                replace_existing=True
            )
            logger.info(f"Added warmup job: {warmup_job_id}, warmup_at: {warmup_at}")
        else:
            # 워밍업 시간이 지났으면 즉시 실행
            logger.warning(f"Warmup time passed, executing immediately")
            warmup_job_id = None
            # 즉시 워밍업 실행은 예약 작업에서 처리

        # 예약 작업 추가
        job = self._scheduler.add_job(
            func=execute_scheduled_reservation,
            trigger=DateTrigger(run_date=execute_at),
            args=[schedule_id],
            id=job_id,
            name=f"Scheduled Reservation #{schedule_id}",
            replace_existing=True
        )

        logger.info(f"Added reservation job: {job_id}, execute_at: {execute_at}")
        return job_id, warmup_job_id

    def remove_job(self, job_id: str):
        """작업 제거"""
        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.debug(f"Job not found or already removed: {job_id}")

    def get_job(self, job_id: str):
        """작업 조회"""
        return self._scheduler.get_job(job_id)

    def get_all_jobs(self):
        """모든 작업 조회"""
        return self._scheduler.get_jobs()

    def pause_job(self, job_id: str):
        """작업 일시 중지"""
        self._scheduler.pause_job(job_id)
        logger.info(f"Paused job: {job_id}")

    def resume_job(self, job_id: str):
        """작업 재개"""
        self._scheduler.resume_job(job_id)
        logger.info(f"Resumed job: {job_id}")


def execute_session_warmup(schedule_id: int):
    """세션 워밍업 실행 (APScheduler에서 호출)

    Args:
        schedule_id: ReservationSchedule ID
    """
    from app import create_app, db
    from app.models.database import ReservationSchedule, CampingSite, CampingSiteAccount
    from app.services.multi_account_reservation_service import MultiAccountReservationService

    app = create_app()

    with app.app_context():
        logger.info(f"========== Session Warmup #{schedule_id} ==========")

        # 스케줄 조회
        schedule = ReservationSchedule.query.get(schedule_id)
        if not schedule:
            logger.error(f"Schedule not found: {schedule_id}")
            return

        if schedule.status == 'cancelled':
            logger.info(f"Schedule #{schedule_id} was cancelled, skipping warmup")
            return

        # 상태 업데이트
        schedule.status = 'warming'
        db.session.commit()

        try:
            # 캠핑장 조회
            camping_site = CampingSite.query.get(schedule.camping_site_id)
            if not camping_site:
                raise Exception(f"Camping site not found: {schedule.camping_site_id}")

            # 계정 필터링
            if schedule.account_ids:
                accounts = CampingSiteAccount.query.filter(
                    CampingSiteAccount.id.in_(schedule.account_ids),
                    CampingSiteAccount.is_active == True
                ).order_by(CampingSiteAccount.priority).all()
            else:
                accounts = CampingSiteAccount.query.filter_by(
                    camping_site_id=schedule.camping_site_id,
                    is_active=True
                ).order_by(CampingSiteAccount.priority).all()

            if not accounts:
                logger.warning(f"No active accounts found for schedule #{schedule_id}")
                return

            logger.info(f"Starting warmup for {len(accounts)} accounts")

            # 워밍업 실행
            service = MultiAccountReservationService()
            warmup_status = service.warmup_sessions(
                schedule_id=schedule_id,
                camping_site=camping_site,
                accounts=accounts,
                execute_at=schedule.execute_at
            )

            logger.info(f"Warmup complete: {warmup_status}")

        except Exception as e:
            logger.error(f"Error in warmup #{schedule_id}: {e}", exc_info=True)


def execute_scheduled_reservation(schedule_id: int):
    """스케줄된 예약 실행 (APScheduler에서 호출) - 고도화 버전

    Args:
        schedule_id: ReservationSchedule ID
    """
    from app import create_app, db
    from app.models.database import ReservationSchedule, CampingSite, CampingSiteAccount, CampingSiteSeat, AppSettings
    from app.services.multi_account_reservation_service import MultiAccountReservationService
    from app.notifications.telegram_notifier import TelegramNotifier

    app = create_app()

    with app.app_context():
        logger.info(f"========== Executing scheduled reservation #{schedule_id} ==========")

        # 스케줄 조회
        schedule = ReservationSchedule.query.get(schedule_id)
        if not schedule:
            logger.error(f"Schedule not found: {schedule_id}")
            return

        if schedule.status == 'cancelled':
            logger.info(f"Schedule #{schedule_id} was cancelled, skipping")
            return

        # 상태 업데이트
        schedule.status = 'running'
        db.session.commit()

        try:
            # 캠핑장 조회
            camping_site = CampingSite.query.get(schedule.camping_site_id)
            if not camping_site:
                raise Exception(f"Camping site not found: {schedule.camping_site_id}")

            # 우선순위 좌석 목록 가져오기
            seat_ids = schedule.get_seat_ids()
            if seat_ids:
                # 순서 유지를 위해 개별 조회
                seats = []
                for seat_id in seat_ids:
                    seat = CampingSiteSeat.query.get(seat_id)
                    if seat:
                        seats.append(seat)
            else:
                seats = []

            # 계정 필터링
            if schedule.account_ids:
                accounts = CampingSiteAccount.query.filter(
                    CampingSiteAccount.id.in_(schedule.account_ids),
                    CampingSiteAccount.is_active == True
                ).order_by(CampingSiteAccount.priority).all()
            else:
                accounts = CampingSiteAccount.query.filter_by(
                    camping_site_id=schedule.camping_site_id,
                    is_active=True
                ).order_by(CampingSiteAccount.priority).all()

            if not accounts:
                raise Exception("No active accounts found")

            logger.info(f"Executing with {len(accounts)} accounts for site: {camping_site.name}")
            logger.info(f"Target date: {schedule.target_date}")
            logger.info(f"Priority seats: {[s.seat_name for s in seats] if seats else 'Any'}")

            # 예약 서비스 호출 (고급 버전)
            service = MultiAccountReservationService()

            # 워밍업이 안 됐으면 즉시 워밍업
            from app.services.session_warmup_service import session_warmup_service
            if not session_warmup_service.get_ready_scrapers(schedule_id):
                logger.warning(f"Sessions not warmed up, executing immediate warmup")
                service.warmup_sessions(
                    schedule_id=schedule_id,
                    camping_site=camping_site,
                    accounts=accounts,
                    execute_at=schedule.execute_at
                )

            # 예약 시간 계산 (execute_at의 시:분)
            reservation_time = schedule.execute_at.strftime('%H:%M')

            # 고급 예약 실행
            result = service.attempt_advanced_reservation(
                schedule_id=schedule_id,
                camping_site=camping_site,
                target_date=str(schedule.target_date),
                seats=seats,
                accounts=accounts,
                wave_interval_ms=schedule.wave_interval_ms or 50,
                burst_retry_count=schedule.burst_retry_count or 3,
                pre_fire_ms=schedule.pre_fire_ms or 0,
                reservation_time=reservation_time,
                dry_run=schedule.dry_run or False
            )

            # 결과 저장
            schedule.result = result

            # 텔레그램 알림 초기화 - DB 설정 우선 사용
            settings = AppSettings.query.first()
            if settings and settings.telegram_bot_token and settings.telegram_chat_id:
                notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
                logger.info(f"Using Telegram settings from database")
            else:
                notifier = TelegramNotifier()  # 환경 변수 fallback
                logger.info(f"Using Telegram settings from environment")

            if result.get('success'):
                schedule.status = 'completed'
                logger.info(f"🎉 Schedule #{schedule_id} completed successfully!")

                # 성공 알림 - first_success에서 정보 가져오기
                first_success = result.get('first_success', {})
                reservation_number = first_success.get('reservation_number', 'N/A')
                selected_seat = first_success.get('selected_seat', '')
                is_dry_run = result.get('dry_run', False) or first_success.get('dry_run', False)

                # DRY_RUN 모드 표시
                if is_dry_run:
                    reservation_number = f"[테스트] {reservation_number}"
                    logger.info(f"🧪 DRY RUN 모드로 테스트 완료")

                notifier.send_reservation_success(
                    camping_site=camping_site.name,
                    date=str(schedule.target_date),
                    reservation_number=reservation_number,
                    seat_name=selected_seat
                )
            else:
                # 재시도 로직
                if schedule.retry_count > 0:
                    schedule.retry_count -= 1
                    schedule.status = 'pending'

                    # 재시도 스케줄 등록
                    retry_time = datetime.now() + timedelta(seconds=schedule.retry_interval)
                    scheduler_service = SchedulerService()
                    scheduler_service.add_reservation_job(schedule_id, retry_time, warmup_minutes=0)

                    logger.info(f"Schedule #{schedule_id} failed, retrying at {retry_time} (remaining: {schedule.retry_count})")
                else:
                    schedule.status = 'failed'
                    logger.error(f"❌ Schedule #{schedule_id} failed after all retries")

                    # 최종 실패 알림
                    error_msg = result.get('error', '알 수 없는 오류')
                    notifier.send_reservation_failure(
                        camping_site=camping_site.name,
                        date=str(schedule.target_date),
                        error=error_msg
                    )

            db.session.commit()

        except Exception as e:
            logger.error(f"Error executing schedule #{schedule_id}: {e}", exc_info=True)
            schedule.status = 'failed'
            schedule.result = {'error': str(e)}
            db.session.commit()

            # 예외 발생 시 실패 알림 - DB 설정 우선 사용
            settings = AppSettings.query.first()
            if settings and settings.telegram_bot_token and settings.telegram_chat_id:
                notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
            else:
                notifier = TelegramNotifier()
            notifier.send_reservation_failure(
                camping_site=camping_site.name if camping_site else '알 수 없음',
                date=str(schedule.target_date) if schedule else '알 수 없음',
                error=str(e)
            )

        finally:
            # 세션 정리
            service = MultiAccountReservationService()
            service.cleanup_sessions(schedule_id)


# 싱글톤 인스턴스
scheduler_service = SchedulerService()
