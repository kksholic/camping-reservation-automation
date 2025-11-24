"""XTicket API 간단 테스트 스크립트 (Flask 종속성 없이)"""
import requests
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수
USER_ID = os.getenv('XTICKET_USER_ID')
PASSWORD = os.getenv('XTICKET_PASSWORD')
SHOP_ENCODE = os.getenv('XTICKET_SHOP_ENCODE')
SHOP_CODE = os.getenv('XTICKET_SHOP_CODE')

BASE_URL = "https://camp.xticket.kr"

def test_login():
    """로그인 테스트"""
    print("\n[1] 로그인 테스트")
    print("-" * 60)

    session = requests.Session()

    # 먼저 메인 페이지 방문하여 세션 생성
    print("   메인 페이지 방문 중...")
    main_url = f"{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}"
    try:
        session.get(main_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        print("   ✓ 세션 생성 완료")
    except Exception as e:
        print(f"   ✗ 메인 페이지 접근 실패: {e}")
        return None

    # 로그인 요청 헤더 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}',
        'Origin': BASE_URL
    })

    url = f"{BASE_URL}/Web/Member/MemberLogin.json"
    payload = {
        "member_id": USER_ID,
        "member_password": PASSWORD,
        "shopCode": SHOP_CODE
    }

    print("   로그인 요청 중...")
    try:
        response = session.post(url, data=urlencode(payload))
        data = response.json()

        if data.get('data', {}).get('success'):
            print(f"✅ 로그인 성공: {data['data'].get('member_id')}")
            print(f"   회원번호: {data['data'].get('member_no')}")
            return session
        else:
            print(f"❌ 로그인 실패")
            print(f"   응답: {data}")
            return None
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_shop_info(session):
    """캠핑장 정보 조회 테스트"""
    print("\n[2] 캠핑장 정보 조회")
    print("-" * 60)

    url = f"{BASE_URL}/Web/Book/GetShopInformation.json"
    payload = {"shop_encode": SHOP_ENCODE}

    try:
        response = session.post(url, data=urlencode(payload))
        data = response.json()

        shop_info = data.get('data', {})
        if shop_info:
            print(f"✅ 캠핑장 이름: {shop_info.get('shop_name')}")
            print(f"   예약 가능 일수: {shop_info.get('book_month_limit_count')}일")
            print(f"   1일 예약 사이트 수: {shop_info.get('book_day_limit_count')}개")
            print(f"   결제 방법: {shop_info.get('web_payment_kind')}")
        else:
            print("❌ 캠핑장 정보 조회 실패")
    except Exception as e:
        print(f"❌ 에러: {e}")


def test_available_dates(session):
    """예약 가능 날짜 조회 테스트"""
    print("\n[3] 예약 가능 날짜 조회")
    print("-" * 60)

    now = datetime.now()
    play_month = f"{now.year}{now.month:02d}"

    url = f"{BASE_URL}/Web/Book/GetBookPlayDate.json"
    payload = {"play_month": play_month}

    try:
        response = session.post(url, data=urlencode(payload))
        data = response.json()

        dates = data.get('data', {}).get('bookPlayDateList', [])

        if dates:
            print(f"✅ 총 {len(dates)}개 날짜 조회됨")

            available_dates = [d for d in dates if d.get('book_remain_count', 0) > 0]
            unavailable_dates = [d for d in dates if d.get('book_remain_count', 0) == 0]

            print(f"\n   예약 가능: {len(available_dates)}개")
            print(f"   예약 불가: {len(unavailable_dates)}개")

            if available_dates:
                print("\n   예약 가능한 날짜 (처음 5개):")
                for date_info in available_dates[:5]:
                    play_date = date_info['play_date']
                    formatted = f"{play_date[:4]}-{play_date[4:6]}-{play_date[6:8]}"
                    print(f"   - {formatted}: 잔여 {date_info['book_remain_count']}개")
        else:
            print("❌ 예약 가능 날짜 조회 실패")
    except Exception as e:
        print(f"❌ 에러: {e}")


def test_product_groups(session):
    """시설 그룹 조회 테스트"""
    print("\n[4] 시설(상품) 그룹 조회")
    print("-" * 60)

    now = datetime.now()
    start_date = f"{now.year}{now.month:02d}01"
    end_date = f"{now.year}{now.month:02d}30"

    url = f"{BASE_URL}/Web/Book/GetBookProductGroup.json"
    payload = {
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        response = session.post(url, data=urlencode(payload))
        data = response.json()

        products = data.get('data', {}).get('bookProductGroupList', [])

        if products:
            print(f"✅ 총 {len(products)}개 시설 그룹 조회됨")
            for product in products:
                print(f"\n   [{product.get('product_group_code')}] {product.get('product_group_name')}")
                print(f"   - 요금: {product.get('product_fee'):,}원")
                if product.get('stay_discount_yn') == '1':
                    print(f"   - 숙박 할인: {product.get('stay_discount_value')}원")
        else:
            print("❌ 시설 그룹 조회 실패")
    except Exception as e:
        print(f"❌ 에러: {e}")


def main():
    print("=" * 60)
    print("XTicket API 테스트")
    print("=" * 60)
    print(f"사용자: {USER_ID}")
    print(f"캠핑장 코드: {SHOP_CODE}")
    print("=" * 60)

    # 로그인
    session = test_login()
    if not session:
        print("\n로그인 실패로 테스트 중단")
        return

    # 각 API 테스트
    test_shop_info(session)
    test_available_dates(session)
    test_product_groups(session)

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
