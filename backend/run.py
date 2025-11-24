"""Flask 애플리케이션 실행"""
import os
from dotenv import load_dotenv
from app import create_app
from loguru import logger

# .env 파일 로드
load_dotenv()

# 환경 설정
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)


if __name__ == '__main__':
    logger.info(f"Starting Flask app in {env} mode")

    # 개발 모드 설정
    debug = env == 'development'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    app.run(
        host=host,
        port=port,
        debug=debug
    )
