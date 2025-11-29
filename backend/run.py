"""Flask 애플리케이션 실행"""
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# .env 파일 로드
load_dotenv()

# 환경 설정
env = os.getenv('FLASK_ENV', 'development')


if __name__ == '__main__':
    try:
        from app import create_app
        app = create_app(env)

        logger.info(f"🚀 서버 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"환경: {env}")

        # 개발 모드 설정
        debug = env == 'development'
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 5000))

        logger.info(f"서버 주소: http://{host}:{port}")

        app.run(
            host=host,
            port=port,
            debug=debug
        )
    except KeyboardInterrupt:
        logger.warning("🛑 서버 종료: 사용자 인터럽트 (Ctrl+C)")
    except SystemExit as e:
        logger.warning(f"🛑 서버 종료: SystemExit (code={e.code})")
    except Exception as e:
        logger.error(f"🛑 서버 비정상 종료: {type(e).__name__}: {e}")
        logger.error(f"상세 오류:\n{traceback.format_exc()}")
        sys.exit(1)
    finally:
        logger.info(f"⏹️ 서버 종료 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
