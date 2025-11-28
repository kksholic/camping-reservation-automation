"""
Check database tables
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app import create_app, db
from app.models.database import ReservationSchedule

app = create_app()

with app.app_context():
    # 테이블 구조 확인
    from sqlalchemy import inspect
    inspector = inspect(db.engine)

    print("📋 Available tables:")
    for table_name in inspector.get_table_names():
        print(f"  - {table_name}")

    if 'reservation_schedules' in inspector.get_table_names():
        print("\n📋 reservation_schedules columns:")
        for column in inspector.get_columns('reservation_schedules'):
            print(f"  - {column['name']} ({column['type']})")
    else:
        print("\n❌ reservation_schedules table does not exist")
