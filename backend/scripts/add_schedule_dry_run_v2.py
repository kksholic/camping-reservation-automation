"""
Add dry_run column to reservation_schedules table using SQLAlchemy
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # dry_run 컬럼이 이미 있는지 확인
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('reservation_schedules')]

        if 'dry_run' in columns:
            print("✅ dry_run column already exists in reservation_schedules table")
        else:
            # dry_run 컬럼 추가
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE reservation_schedules
                    ADD COLUMN dry_run BOOLEAN DEFAULT 0
                """))
                conn.commit()
            print("✅ Successfully added dry_run column to reservation_schedules table")

        # 결과 확인
        inspector = inspect(db.engine)
        print("\n📋 reservation_schedules table structure:")
        for col in inspector.get_columns('reservation_schedules'):
            print(f"  - {col['name']} ({col['type']})")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
