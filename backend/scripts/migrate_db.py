"""
데이터베이스 마이그레이션 스크립트
새 컬럼 추가: seat_ids, wave_interval_ms, burst_retry_count, pre_fire_ms, session_warmup_minutes, warmup_job_id
"""
import sqlite3
import os

# 데이터베이스 경로 (프로젝트 루트의 data 폴더)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'camping.db')

def run_migration():
    """새 컬럼들을 reservation_schedules 테이블에 추가"""
    print(f"Database path: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 현재 테이블 스키마 확인
    cursor.execute("PRAGMA table_info(reservation_schedules)")
    columns = {row[1] for row in cursor.fetchall()}
    print(f"Current columns: {columns}")

    migrations = [
        ("seat_ids", "TEXT"),  # JSON 배열
        ("wave_interval_ms", "INTEGER DEFAULT 50"),
        ("burst_retry_count", "INTEGER DEFAULT 3"),
        ("pre_fire_ms", "INTEGER DEFAULT 0"),
        ("session_warmup_minutes", "INTEGER DEFAULT 5"),
        ("warmup_job_id", "VARCHAR(100)"),
    ]

    for col_name, col_type in migrations:
        if col_name not in columns:
            sql = f"ALTER TABLE reservation_schedules ADD COLUMN {col_name} {col_type}"
            print(f"Running: {sql}")
            cursor.execute(sql)
        else:
            print(f"Column {col_name} already exists, skipping")

    conn.commit()
    conn.close()
    print("Migration completed!")

if __name__ == "__main__":
    run_migration()
