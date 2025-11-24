"""XTicket API 테스트 스크립트"""
import sys
import os
from datetime import datetime

# backend 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from app.scrapers.xticket_scraper import XTicketScraper
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def main():
    # 환경 변수에서 설정 읽기
    user_id = os.getenv('XTICKET_USER_ID')
    password = os.getenv('XTICKET_PASSWORD')
    shop_encode = os.getenv('XTICKET_SHOP_ENCODE')
    shop_code = os.getenv('XTICKET_SHOP_CODE')

    print("=" * 60)
    print("XTicket API 테스트")
    print("=" * 60)
    print(f"사용자: {user_id}")
    print(f"캠핑장 코드: {shop_code}")
    print("=" * 60)

    # 스크래퍼 인스턴스 생성
    with XTicketScraper(shop_encode, shop_code) as scraper:

        # 1. 로그인 테스트
        print("\n[1] 로그인 테스트")
        print("-" * 60)
        success = scraper.login(user_id, password)
        if success:
            print("✅ 로그인 성공")
        else:
            print("❌ 로그인 실패")
            return

        # 2. 캠핑장 정보 조회
        print("\n[2] 캠핑장 정보 조회")
        print("-" * 60)
        shop_info = scraper.get_shop_information()
        if shop_info:
            print(f"✅ 캠핑장 이름: {shop_info.get('shop_name')}")
            print(f"   예약 가능 일수: {shop_info.get('book_month_limit_count')}일")
            print(f"   1일 예약 사이트 수: {shop_info.get('book_day_limit_count')}개")
            print(f"   결제 방법: {shop_info.get('web_payment_kind')}")
        else:
            print("❌ 캠핑장 정보 조회 실패")

        # 3. 예약 가능 날짜 조회 (이번 달)
        print("\n[3] 예약 가능 날짜 조회")
        print("-" * 60)
        now = datetime.now()
        dates = scraper.get_available_dates(now.year, now.month)

        if dates:
            print(f"✅ 총 {len(dates)}개 날짜 조회됨")

            # 예약 가능한 날짜만 필터링
            available_dates = [d for d in dates if d['available']]
            unavailable_dates = [d for d in dates if not d['available']]

            print(f"\n   예약 가능: {len(available_dates)}개")
            print(f"   예약 불가: {len(unavailable_dates)}개")

            # 예약 가능한 날짜 일부 출력
            if available_dates:
                print("\n   예약 가능한 날짜 (처음 5개):")
                for date_info in available_dates[:5]:
                    print(f"   - {date_info['date']}: 잔여 {date_info['remain_count']}개")
        else:
            print("❌ 예약 가능 날짜 조회 실패")

        # 4. 시설 그룹 조회
        print("\n[4] 시설(상품) 그룹 조회")
        print("-" * 60)

        # 이번 달 시작일과 종료일 계산
        start_date = f"{now.year}{now.month:02d}01"

        # 다음 달의 전날까지
        if now.month == 12:
            next_year = now.year + 1
            next_month = 1
        else:
            next_year = now.year
            next_month = now.month + 1

        from datetime import date
        last_day = date(next_year, next_month, 1).day - 1
        end_date = f"{now.year}{now.month:02d}{last_day}"

        products = scraper.get_product_groups(start_date, end_date)

        if products:
            print(f"✅ 총 {len(products)}개 시설 그룹 조회됨")
            for product in products:
                print(f"\n   [{product.get('product_group_code')}] {product.get('product_group_name')}")
                print(f"   - 요금: {product.get('product_fee'):,}원")
                if product.get('stay_discount_yn') == '1':
                    print(f"   - 숙박 할인: {product.get('stay_discount_value')}원")
        else:
            print("❌ 시설 그룹 조회 실패")

        # 5. 특정 날짜 예약 가능 여부 확인
        print("\n[5] 특정 날짜 예약 가능 여부 확인")
        print("-" * 60)

        # 오늘부터 7일 후 날짜
        from datetime import timedelta
        target_date = now + timedelta(days=7)
        target_date_str = target_date.strftime('%Y-%m-%d')

        is_available = scraper.check_availability(target_date_str)
        if is_available:
            print(f"✅ {target_date_str} - 예약 가능")
        else:
            print(f"❌ {target_date_str} - 예약 불가")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
