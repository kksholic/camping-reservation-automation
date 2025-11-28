"""
Add dry_run column to reservation_schedules table
"""
import sqlite3
import os
from pathlib import Path

def main():
    # 프로젝트 루트 경로 찾기
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    db_path = backend_dir / 'data' / 'camping.db'

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    print(f"📂 Database path: {db_path}")

    # DB 연결
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # dry_run 컬럼이 이미 있는지 확인
        cursor.execute("PRAGMA table_info(reservation_schedules)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'dry_run' in columns:
            print("✅ dry_run column already exists in reservation_schedules table")
        else:
            # dry_run 컬럼 추가
            cursor.execute("""
                ALTER TABLE reservation_schedules
                ADD COLUMN dry_run BOOLEAN DEFAULT 0
            """)
            conn.commit()
            print("✅ Successfully added dry_run column to reservation_schedules table")

        # 결과 확인
        cursor.execute("PRAGMA table_info(reservation_schedules)")
        print("\n📋 reservation_schedules table structure:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
