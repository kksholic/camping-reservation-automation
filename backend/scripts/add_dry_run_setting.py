"""AppSettings에 xticket_dry_run 필드 추가 마이그레이션"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.database import AppSettings
from loguru import logger

def migrate():
    """xticket_dry_run 컬럼 추가"""
    app = create_app()

    with app.app_context():
        try:
            # SQLite에서는 ALTER TABLE ADD COLUMN이 제한적이므로
            # SQLAlchemy의 반영 기능 사용
            from sqlalchemy import inspect, Boolean

            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('app_settings')]

            if 'xticket_dry_run' not in columns:
                logger.info("Adding xticket_dry_run column to app_settings table...")

                # SQLite는 ALTER TABLE ADD COLUMN 지원
                with db.engine.connect() as conn:
                    conn.execute(db.text(
                        "ALTER TABLE app_settings ADD COLUMN xticket_dry_run BOOLEAN DEFAULT 0"
                    ))
                    conn.commit()

                logger.success("✅ Column added successfully!")

                # 기존 레코드의 기본값 설정
                settings = AppSettings.query.first()
                if settings and settings.xticket_dry_run is None:
                    settings.xticket_dry_run = False
                    db.session.commit()
                    logger.info("Default value set for existing record")
            else:
                logger.info("Column xticket_dry_run already exists, skipping migration")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
