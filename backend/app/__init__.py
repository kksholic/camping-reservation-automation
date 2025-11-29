"""Flask 애플리케이션 팩토리"""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from loguru import logger
import sys
import os
import atexit
import signal
from datetime import timedelta
from pathlib import Path

from config import config


# 확장 초기화
db = SQLAlchemy()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def _setup_shutdown_handlers():
    """서버 종료 시 로그 남기기"""
    def on_exit():
        logger.warning("🛑 서버 종료: atexit 호출 (정상 종료)")

    def signal_handler(signum, frame):
        signal_names = {
            signal.SIGINT: 'SIGINT (Ctrl+C)',
            signal.SIGTERM: 'SIGTERM (종료 요청)',
        }
        # Windows에서는 SIGHUP이 없음
        if hasattr(signal, 'SIGHUP'):
            signal_names[signal.SIGHUP] = 'SIGHUP (터미널 종료)'

        sig_name = signal_names.get(signum, f'Signal {signum}')
        logger.warning(f"🛑 서버 종료: {sig_name} 수신")
        sys.exit(0)

    # atexit 등록
    atexit.register(on_exit)

    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Windows에서는 SIGHUP 없음
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)


def create_app(config_name='default'):
    """Flask 애플리케이션 생성"""
    app = Flask(__name__)

    # 설정 로드
    app.config.from_object(config[config_name])

    # 로그 파일 디렉토리 자동 생성
    log_file = app.config['LOG_FILE']
    log_dir = Path(log_file).parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 로그 디렉토리 생성: {log_dir}")

    # 로깅 설정 - 기존 핸들러 모두 제거 후 새로 설정
    logger.remove()

    # stdout 핸들러 (컬러 출력)
    logger.add(
        sys.stdout,
        level=app.config['LOG_LEVEL'],
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # 파일 핸들러 (영구 기록)
    logger.add(
        log_file,
        rotation="1 day",
        retention="7 days",
        level=app.config['LOG_LEVEL'],
        encoding='utf-8',
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        backtrace=True,
        diagnose=True
    )

    logger.info(f"📝 로그 파일: {log_file}")

    # 종료 핸들러 설정
    _setup_shutdown_handlers()

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

    # 스케줄러 시작 (reloader 프로세스가 아닌 경우에만)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        from app.services.scheduler_service import scheduler_service
        scheduler_service.start()
        logger.info("Scheduler service started")

    logger.info(f"Flask app created with config: {config_name}")

    return app
