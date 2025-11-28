"""
생림오토캠핑장 좌석 데이터 초기화 스크립트
"""
import sys
import os

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.database import CampingSite, CampingSiteSeat

# 생림오토캠핑장 전체 좌석 목록 (실제 사이트 정보 기반)
SAENGRIM_SEATS = [
    # 잔디사이트 (product_group_code: 0001)
    {"product_code": "00010001", "product_group_code": "0001", "seat_name": "금관-01", "seat_category": "grass", "display_order": 1},
    {"product_code": "00010002", "product_group_code": "0001", "seat_name": "금관-02", "seat_category": "grass", "display_order": 2},
    {"product_code": "00010003", "product_group_code": "0001", "seat_name": "금관-03", "seat_category": "grass", "display_order": 3},
    {"product_code": "00010004", "product_group_code": "0001", "seat_name": "금관-04", "seat_category": "grass", "display_order": 4},
    {"product_code": "00010005", "product_group_code": "0001", "seat_name": "금관-05", "seat_category": "grass", "display_order": 5},
    {"product_code": "00010006", "product_group_code": "0001", "seat_name": "금관-06", "seat_category": "grass", "display_order": 6},
    {"product_code": "00010007", "product_group_code": "0001", "seat_name": "금관-07", "seat_category": "grass", "display_order": 7},
    {"product_code": "00010008", "product_group_code": "0001", "seat_name": "금관-08", "seat_category": "grass", "display_order": 8},
    {"product_code": "00010009", "product_group_code": "0001", "seat_name": "금관-09", "seat_category": "grass", "display_order": 9},
    {"product_code": "00010010", "product_group_code": "0001", "seat_name": "금관-10", "seat_category": "grass", "display_order": 10},
    {"product_code": "00010011", "product_group_code": "0001", "seat_name": "금관-11", "seat_category": "grass", "display_order": 11},
    {"product_code": "00010012", "product_group_code": "0001", "seat_name": "금관-12", "seat_category": "grass", "display_order": 12},
    {"product_code": "00010013", "product_group_code": "0001", "seat_name": "금관-13", "seat_category": "grass", "display_order": 13},
    {"product_code": "00010014", "product_group_code": "0001", "seat_name": "금관-14", "seat_category": "grass", "display_order": 14},
    {"product_code": "00010015", "product_group_code": "0001", "seat_name": "금관-15", "seat_category": "grass", "display_order": 15},
    {"product_code": "00010016", "product_group_code": "0001", "seat_name": "금관-16", "seat_category": "grass", "display_order": 16},
    {"product_code": "00010017", "product_group_code": "0001", "seat_name": "금관-17", "seat_category": "grass", "display_order": 17},
    {"product_code": "00010018", "product_group_code": "0001", "seat_name": "금관-18", "seat_category": "grass", "display_order": 18},
    {"product_code": "00010019", "product_group_code": "0001", "seat_name": "금관-19", "seat_category": "grass", "display_order": 19},
    {"product_code": "00010020", "product_group_code": "0001", "seat_name": "금관-20", "seat_category": "grass", "display_order": 20},

    # 데크사이트 (product_group_code: 0002)
    {"product_code": "00020001", "product_group_code": "0002", "seat_name": "데크-01", "seat_category": "deck", "display_order": 101},
    {"product_code": "00020002", "product_group_code": "0002", "seat_name": "데크-02", "seat_category": "deck", "display_order": 102},
    {"product_code": "00020003", "product_group_code": "0002", "seat_name": "데크-03", "seat_category": "deck", "display_order": 103},
    {"product_code": "00020004", "product_group_code": "0002", "seat_name": "데크-04", "seat_category": "deck", "display_order": 104},
    {"product_code": "00020005", "product_group_code": "0002", "seat_name": "데크-05", "seat_category": "deck", "display_order": 105},
    {"product_code": "00020006", "product_group_code": "0002", "seat_name": "데크-06", "seat_category": "deck", "display_order": 106},
    {"product_code": "00020007", "product_group_code": "0002", "seat_name": "데크-07", "seat_category": "deck", "display_order": 107},
    {"product_code": "00020008", "product_group_code": "0002", "seat_name": "데크-08", "seat_category": "deck", "display_order": 108},
    {"product_code": "00020009", "product_group_code": "0002", "seat_name": "데크-09", "seat_category": "deck", "display_order": 109},
    {"product_code": "00020010", "product_group_code": "0002", "seat_name": "데크-10", "seat_category": "deck", "display_order": 110},
    {"product_code": "00020011", "product_group_code": "0002", "seat_name": "데크-11", "seat_category": "deck", "display_order": 111},
    {"product_code": "00020012", "product_group_code": "0002", "seat_name": "데크-12", "seat_category": "deck", "display_order": 112},
    {"product_code": "00020013", "product_group_code": "0002", "seat_name": "데크-13", "seat_category": "deck", "display_order": 113},
    {"product_code": "00020014", "product_group_code": "0002", "seat_name": "데크-14", "seat_category": "deck", "display_order": 114},
    {"product_code": "00020015", "product_group_code": "0002", "seat_name": "데크-15", "seat_category": "deck", "display_order": 115},

    # 파쇄석사이트 (product_group_code: 0004)
    {"product_code": "00040001", "product_group_code": "0004", "seat_name": "금관-01", "seat_category": "crushed_stone", "display_order": 201},
    {"product_code": "00040002", "product_group_code": "0004", "seat_name": "금관-02", "seat_category": "crushed_stone", "display_order": 202},
    {"product_code": "00040003", "product_group_code": "0004", "seat_name": "금관-03", "seat_category": "crushed_stone", "display_order": 203},
    {"product_code": "00040004", "product_group_code": "0004", "seat_name": "금관-04", "seat_category": "crushed_stone", "display_order": 204},
    {"product_code": "00040005", "product_group_code": "0004", "seat_name": "금관-05", "seat_category": "crushed_stone", "display_order": 205},
    {"product_code": "00040006", "product_group_code": "0004", "seat_name": "금관-06", "seat_category": "crushed_stone", "display_order": 206},
    {"product_code": "00040007", "product_group_code": "0004", "seat_name": "금관-07", "seat_category": "crushed_stone", "display_order": 207},
    {"product_code": "00040008", "product_group_code": "0004", "seat_name": "금관-08", "seat_category": "crushed_stone", "display_order": 208},
    {"product_code": "00040009", "product_group_code": "0004", "seat_name": "금관-09", "seat_category": "crushed_stone", "display_order": 209},
    {"product_code": "00040010", "product_group_code": "0004", "seat_name": "금관-10", "seat_category": "crushed_stone", "display_order": 210},
    {"product_code": "00040011", "product_group_code": "0004", "seat_name": "금관-11", "seat_category": "crushed_stone", "display_order": 211},
    {"product_code": "00040012", "product_group_code": "0004", "seat_name": "금관-12", "seat_category": "crushed_stone", "display_order": 212},
    {"product_code": "00040013", "product_group_code": "0004", "seat_name": "금관-13", "seat_category": "crushed_stone", "display_order": 213},
    {"product_code": "00040014", "product_group_code": "0004", "seat_name": "금관-14", "seat_category": "crushed_stone", "display_order": 214},
    {"product_code": "00040015", "product_group_code": "0004", "seat_name": "금관-15", "seat_category": "crushed_stone", "display_order": 215},
    {"product_code": "00040016", "product_group_code": "0004", "seat_name": "금관-16", "seat_category": "crushed_stone", "display_order": 216},
    {"product_code": "00040017", "product_group_code": "0004", "seat_name": "금관-17", "seat_category": "crushed_stone", "display_order": 217},
    {"product_code": "00040018", "product_group_code": "0004", "seat_name": "금관-18", "seat_category": "crushed_stone", "display_order": 218},
    {"product_code": "00040019", "product_group_code": "0004", "seat_name": "금관-19", "seat_category": "crushed_stone", "display_order": 219},
    {"product_code": "00040020", "product_group_code": "0004", "seat_name": "금관-20", "seat_category": "crushed_stone", "display_order": 220},
    {"product_code": "00040021", "product_group_code": "0004", "seat_name": "금관-21", "seat_category": "crushed_stone", "display_order": 221},
    {"product_code": "00040022", "product_group_code": "0004", "seat_name": "금관-22", "seat_category": "crushed_stone", "display_order": 222},
    {"product_code": "00040023", "product_group_code": "0004", "seat_name": "금관-23", "seat_category": "crushed_stone", "display_order": 223},
    {"product_code": "00040024", "product_group_code": "0004", "seat_name": "금관-24", "seat_category": "crushed_stone", "display_order": 224},
    {"product_code": "00040025", "product_group_code": "0004", "seat_name": "금관-25", "seat_category": "crushed_stone", "display_order": 225},
]


def init_saengrim_seats():
    """생림오토캠핑장 좌석 데이터 초기화"""
    app = create_app()

    with app.app_context():
        # 생림오토캠핑장 찾기 (이름으로 식별)
        saengrim = CampingSite.query.filter(
            CampingSite.name.like('%생림%')
        ).first()

        if not saengrim:
            print("❌ 생림오토캠핑장을 찾을 수 없습니다.")
            print("먼저 캠핑장을 등록해주세요.")
            return

        print(f"✅ 캠핑장 찾음: {saengrim.name} (ID: {saengrim.id})")

        # 기존 좌석 데이터 삭제
        existing_count = CampingSiteSeat.query.filter_by(camping_site_id=saengrim.id).count()
        if existing_count > 0:
            print(f"⚠️  기존 좌석 데이터 {existing_count}개 삭제 중...")
            CampingSiteSeat.query.filter_by(camping_site_id=saengrim.id).delete()
            db.session.commit()

        # 새 좌석 데이터 삽입
        print(f"📝 {len(SAENGRIM_SEATS)}개 좌석 데이터 삽입 중...")

        for seat_data in SAENGRIM_SEATS:
            seat = CampingSiteSeat(
                camping_site_id=saengrim.id,
                product_code=seat_data['product_code'],
                product_group_code=seat_data['product_group_code'],
                seat_name=seat_data['seat_name'],
                seat_category=seat_data['seat_category'],
                display_order=seat_data['display_order']
            )
            db.session.add(seat)

        db.session.commit()

        # 결과 확인
        grass_count = CampingSiteSeat.query.filter_by(
            camping_site_id=saengrim.id,
            seat_category='grass'
        ).count()
        deck_count = CampingSiteSeat.query.filter_by(
            camping_site_id=saengrim.id,
            seat_category='deck'
        ).count()
        crushed_stone_count = CampingSiteSeat.query.filter_by(
            camping_site_id=saengrim.id,
            seat_category='crushed_stone'
        ).count()

        print(f"\n✅ 좌석 데이터 삽입 완료!")
        print(f"   - 잔디사이트: {grass_count}개")
        print(f"   - 데크사이트: {deck_count}개")
        print(f"   - 파쇄석사이트: {crushed_stone_count}개")
        print(f"   - 총 {grass_count + deck_count + crushed_stone_count}개")


if __name__ == '__main__':
    init_saengrim_seats()
