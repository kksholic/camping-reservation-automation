"""데이터베이스 모델"""
from datetime import datetime
from app import db


class CampingSite(db.Model):
    """캠핑장 정보"""
    __tablename__ = 'camping_sites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    site_type = db.Column(db.String(50), nullable=False)  # gocamp, naver, custom
    url = db.Column(db.String(500), nullable=False)

    # 캠핑장 로그인 정보
    login_username = db.Column(db.String(100))
    login_password = db.Column(db.String(200))

    # 예약자 정보
    booker_name = db.Column(db.String(100))
    booker_phone = db.Column(db.String(20))
    booker_car_number = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관계
    reservations = db.relationship('Reservation', backref='camping_site', lazy=True, cascade='all, delete-orphan')
    monitoring_targets = db.relationship('MonitoringTarget', backref='camping_site', lazy=True, cascade='all, delete-orphan')
    accounts = db.relationship('CampingSiteAccount', backref='camping_site', lazy=True, cascade='all, delete-orphan')
    seats = db.relationship('CampingSiteSeat', backref='camping_site', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'site_type': self.site_type,
            'url': self.url,
            'login_username': self.login_username,
            'login_password': self.login_password,
            'booker_name': self.booker_name,
            'booker_phone': self.booker_phone,
            'booker_car_number': self.booker_car_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'accounts_count': len(self.accounts) if self.accounts else 0
        }


class Reservation(db.Model):
    """예약 정보"""
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    camping_site_id = db.Column(db.Integer, db.ForeignKey('camping_sites.id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='monitoring')  # monitoring, available, reserved, failed
    reservation_number = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'camping_site_id': self.camping_site_id,
            'camping_site_name': self.camping_site.name if self.camping_site else None,
            'check_in_date': self.check_in_date.isoformat() if self.check_in_date else None,
            'check_out_date': self.check_out_date.isoformat() if self.check_out_date else None,
            'status': self.status,
            'reservation_number': self.reservation_number,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MonitoringTarget(db.Model):
    """모니터링 타겟"""
    __tablename__ = 'monitoring_targets'

    id = db.Column(db.Integer, primary_key=True)
    camping_site_id = db.Column(db.Integer, db.ForeignKey('camping_sites.id'), nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    notification_sent = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime)
    last_status = db.Column(db.String(50))  # available, unavailable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'camping_site_id': self.camping_site_id,
            'camping_site_name': self.camping_site.name if self.camping_site else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'is_active': self.is_active,
            'notification_sent': self.notification_sent,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'last_status': self.last_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserInfo(db.Model):
    """사용자 정보"""
    __tablename__ = 'user_info'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    car_number = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'car_number': self.car_number,
            'email': self.email
        }


class Admin(db.Model):
    """관리자 계정"""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AppSettings(db.Model):
    """앱 설정"""
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)
    telegram_bot_token = db.Column(db.String(200))
    telegram_chat_id = db.Column(db.String(100))
    xticket_dry_run = db.Column(db.Boolean, default=False)  # DRY_RUN 모드 설정
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'telegram_bot_token': self.telegram_bot_token,
            'telegram_chat_id': self.telegram_chat_id,
            'xticket_dry_run': self.xticket_dry_run,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CampingSiteAccount(db.Model):
    """캠핑장 계정 정보 (1:N 관계)"""
    __tablename__ = 'camping_site_accounts'

    id = db.Column(db.Integer, primary_key=True)
    camping_site_id = db.Column(db.Integer, db.ForeignKey('camping_sites.id'), nullable=False)

    # 캠핑장 로그인 정보
    login_username = db.Column(db.String(100), nullable=False)
    login_password = db.Column(db.String(200), nullable=False)

    # 예약자 정보
    booker_name = db.Column(db.String(100), nullable=False)
    booker_phone = db.Column(db.String(20), nullable=False)
    booker_car_number = db.Column(db.String(20))

    # 계정 관리
    is_active = db.Column(db.Boolean, default=True)  # 활성화 여부
    priority = db.Column(db.Integer, default=0)  # 우선순위 (낮을수록 먼저 시도)
    nickname = db.Column(db.String(100))  # 계정 별칭 (예: "내 계정", "엄마 계정")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'camping_site_id': self.camping_site_id,
            'login_username': self.login_username,
            'login_password': self.login_password,
            'booker_name': self.booker_name,
            'booker_phone': self.booker_phone,
            'booker_car_number': self.booker_car_number,
            'is_active': self.is_active,
            'priority': self.priority,
            'nickname': self.nickname,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CampingSiteSeat(db.Model):
    """캠핑장 좌석 정보 (하드코딩된 전체 좌석 목록)"""
    __tablename__ = 'camping_site_seats'

    id = db.Column(db.Integer, primary_key=True)
    camping_site_id = db.Column(db.Integer, db.ForeignKey('camping_sites.id'), nullable=False)

    # 좌석 정보
    product_code = db.Column(db.String(20), nullable=False)  # 예: 00040009
    product_group_code = db.Column(db.String(10), nullable=False)  # 0001=잔디, 0002=데크, 0004=파쇄석
    seat_name = db.Column(db.String(100), nullable=False)  # 예: 금관-09
    seat_category = db.Column(db.String(50), nullable=False)  # grass, deck, crushed_stone

    # 좌석 상세 정보
    capacity = db.Column(db.Integer)  # 수용 인원
    price = db.Column(db.Integer)  # 가격
    description = db.Column(db.Text)  # 설명

    # 정렬 순서
    display_order = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'camping_site_id': self.camping_site_id,
            'product_code': self.product_code,
            'product_group_code': self.product_group_code,
            'seat_name': self.seat_name,
            'seat_category': self.seat_category,
            'capacity': self.capacity,
            'price': self.price,
            'description': self.description,
            'display_order': self.display_order
        }


class ReservationSchedule(db.Model):
    """예약 스케줄 (특정 시간에 자동 예약 실행)"""
    __tablename__ = 'reservation_schedules'

    id = db.Column(db.Integer, primary_key=True)
    camping_site_id = db.Column(db.Integer, db.ForeignKey('camping_sites.id'), nullable=False)

    # 실행 시간 (예약 오픈 시간)
    execute_at = db.Column(db.DateTime, nullable=False)

    # 예약 타겟 정보
    target_date = db.Column(db.Date, nullable=False)  # 예약하려는 날짜

    # 우선순위 좌석 풀 (JSON 배열: [seat_id_1, seat_id_2, seat_id_3])
    # 1순위 좌석 실패 시 2순위, 3순위 순으로 시도
    seat_ids = db.Column(db.JSON)  # 다중 좌석 지원

    # 하위 호환성을 위한 단일 좌석 (deprecated, seat_ids 사용 권장)
    seat_id = db.Column(db.Integer, db.ForeignKey('camping_site_seats.id'))

    # 사용할 계정 (JSON 배열: [1, 2, 3])
    account_ids = db.Column(db.JSON)

    # 재시도 설정
    retry_count = db.Column(db.Integer, default=3)
    retry_interval = db.Column(db.Integer, default=30)  # 초

    # 고급 설정
    wave_interval_ms = db.Column(db.Integer, default=50)  # Wave Attack 간격 (ms)
    burst_retry_count = db.Column(db.Integer, default=3)  # Burst Retry 횟수
    pre_fire_ms = db.Column(db.Integer, default=0)  # Pre-fire 시간 (ms)
    session_warmup_minutes = db.Column(db.Integer, default=5)  # 세션 워밍업 시작 시간 (분 전)
    dry_run = db.Column(db.Boolean, default=False)  # DRY_RUN 모드 (테스트)

    # 상태
    status = db.Column(db.String(50), default='pending')  # pending, warming, running, completed, failed, cancelled
    result = db.Column(db.JSON)  # 실행 결과

    # APScheduler job IDs (메인 작업 + 워밍업 작업)
    job_id = db.Column(db.String(100))
    warmup_job_id = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    camping_site = db.relationship('CampingSite', backref='schedules')
    seat = db.relationship('CampingSiteSeat')

    def get_seat_ids(self):
        """우선순위 좌석 ID 목록 반환 (하위 호환성 지원)"""
        if self.seat_ids:
            return self.seat_ids
        elif self.seat_id:
            return [self.seat_id]
        return []

    def get_seats(self):
        """우선순위 좌석 객체 목록 반환"""
        seat_ids = self.get_seat_ids()
        if not seat_ids:
            return []
        return CampingSiteSeat.query.filter(CampingSiteSeat.id.in_(seat_ids)).all()

    def to_dict(self):
        # 좌석 정보 구성
        seats_info = []
        for seat_id in self.get_seat_ids():
            seat = CampingSiteSeat.query.get(seat_id)
            if seat:
                seats_info.append({
                    'id': seat.id,
                    'seat_name': seat.seat_name,
                    'product_code': seat.product_code,
                    'seat_category': seat.seat_category
                })

        return {
            'id': self.id,
            'camping_site_id': self.camping_site_id,
            'camping_site_name': self.camping_site.name if self.camping_site else None,
            'execute_at': self.execute_at.isoformat() if self.execute_at else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'seat_ids': self.get_seat_ids(),
            'seats': seats_info,
            # 하위 호환성
            'seat_id': self.seat_id,
            'seat_name': self.seat.seat_name if self.seat else (seats_info[0]['seat_name'] if seats_info else None),
            'account_ids': self.account_ids,
            'retry_count': self.retry_count,
            'retry_interval': self.retry_interval,
            # 고급 설정
            'wave_interval_ms': self.wave_interval_ms,
            'burst_retry_count': self.burst_retry_count,
            'pre_fire_ms': self.pre_fire_ms,
            'session_warmup_minutes': self.session_warmup_minutes,
            'dry_run': self.dry_run,
            'status': self.status,
            'result': self.result,
            'job_id': self.job_id,
            'warmup_job_id': self.warmup_job_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
