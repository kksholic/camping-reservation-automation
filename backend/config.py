"""Flask 애플리케이션 설정"""
import os
from datetime import timedelta


class Config:
    """기본 설정"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # 데이터베이스
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///../../data/camping.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # 텔레그램
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    # XTicket (생림오토 캠핑장 등)
    XTICKET_SHOP_ENCODE = os.getenv('XTICKET_SHOP_ENCODE')
    XTICKET_SHOP_CODE = os.getenv('XTICKET_SHOP_CODE')
    XTICKET_USERNAME = os.getenv('XTICKET_USERNAME')
    XTICKET_PASSWORD = os.getenv('XTICKET_PASSWORD')
    XTICKET_DRY_RUN = os.getenv('XTICKET_DRY_RUN', 'true').lower() == 'true'

    # 모니터링 설정
    MONITORING_INTERVAL = int(os.getenv('MONITORING_INTERVAL', 60))  # 초
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))  # 초

    # 스케줄링 설정
    RESERVATION_SCHEDULE_ENABLED = os.getenv('RESERVATION_SCHEDULE_ENABLED', 'false').lower() == 'true'
    RESERVATION_HOUR = int(os.getenv('RESERVATION_HOUR', 9))  # 기본 오전 9시
    RESERVATION_MINUTE = int(os.getenv('RESERVATION_MINUTE', 0))
    RESERVATION_SECOND = int(os.getenv('RESERVATION_SECOND', 0))

    # 브라우저 설정
    BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
    BROWSER_USER_DATA_DIR = os.getenv('BROWSER_USER_DATA_DIR', './browser_data')

    # 로깅
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    # backend/logs/app.log 경로 사용
    LOG_FILE = os.getenv('LOG_FILE', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'app.log'))

    # 자동 예약 설정
    AUTO_RESERVE_ENABLED = os.getenv('AUTO_RESERVE_ENABLED', 'true').lower() == 'true'
    AUTO_PAY = os.getenv('AUTO_PAY', 'false').lower() == 'true'
    CONFIRMATION_REQUIRED = os.getenv('CONFIRMATION_REQUIRED', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    BROWSER_HEADLESS = False


class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    BROWSER_HEADLESS = True


class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
