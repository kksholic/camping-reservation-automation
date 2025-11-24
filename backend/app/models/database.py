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
