"""Flask 애플리케이션 팩토리"""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from loguru import logger
import sys
from datetime import timedelta

from config import config


# 확장 초기화
db = SQLAlchemy()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def create_app(config_name='default'):
    """Flask 애플리케이션 생성"""
    app = Flask(__name__)

    # 설정 로드
    app.config.from_object(config[config_name])

    # 로깅 설정
    logger.remove()
    logger.add(
        sys.stdout,
        level=app.config['LOG_LEVEL'],
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    logger.add(
        app.config['LOG_FILE'],
        rotation="1 day",
        retention="7 days",
        level=app.config['LOG_LEVEL']
    )

    # 세션 보안 설정
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript에서 쿠키 접근 차단
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF 보호
    # 프로덕션에서는 HTTPS 사용 시 True로 설정
    app.config['SESSION_COOKIE_SECURE'] = False  # development용
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 24시간 후 만료

    # 확장 초기화
    db.init_app(app)
    limiter.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

    # 블루프린트 등록
    from app.api import routes
    app.register_blueprint(routes.bp)

    # 데이터베이스 초기화
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")

        # 기본 관리자 계정 생성
        from app.utils.auth import create_default_admin
        create_default_admin()

    logger.info(f"Flask app created with config: {config_name}")

    return app
