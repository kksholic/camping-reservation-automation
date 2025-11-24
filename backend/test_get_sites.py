"""생림오토캠핑장 좌석 데이터 조회 테스트"""
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

SHOP_ENCODE = os.getenv('XTICKET_SHOP_ENCODE')
SHOP_CODE = os.getenv('XTICKET_SHOP_CODE')
USER_ID = os.getenv('XTICKET_USER_ID')
PASSWORD = os.getenv('XTICKET_PASSWORD')

BASE_URL = "https://camp.xticket.kr"

def main():
    print("="*60)
    print("생림오토캠핑장 좌석 데이터 조회")
    print("="*60)

    # 세션 생성
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}',
        'Origin': BASE_URL
    })

    # 메인 페이지 방문
    print("\n1. 메인 페이지 방문...")
    session.get(f"{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}")
    print("   ✓ 완료")

    # 로그인
    print("\n2. 로그인 중...")
    login_url = f"{BASE_URL}/Web/Member/MemberLogin.json"
    login_data = {
        "member_id": USER_ID,
        "member_password": PASSWORD,
        "shopCode": SHOP_CODE
    }

    response = session.post(login_url, data=login_data)
    login_result = response.json()

    if not login_result.get('data', {}).get('success'):
        print(f"   ❌ 로그인 실패: {login_result}")
        return

    print(f"   ✅ 로그인 성공")

    # 좌석 데이터 조회
    print("\n3. 2025-11-21 좌석 데이터 조회 중...")
    url = f"{BASE_URL}/Web/Book/GetBookProduct010001.json"
    payload = {
        "product_group_code": "0004",
        "start_date": "20251121",
        "end_date": "20251121",
        "book_days": 1,
        "two_stay_days": 0,
        "shopCode": SHOP_CODE
    }

    response = session.post(url, data=payload)
    data = response.json()

    sites = data.get('data', {}).get('bookProductList', [])

    print(f"\n📋 총 {len(sites)}개의 좌석:")
    print("\n" + "="*60)

    # 처음 5개 상세 정보 출력
    for i, site in enumerate(sites[:5], 1):
        print(f"\n[{i}] 좌석 정보:")
        print(f"  - 코드: {site.get('product_code')}")
        print(f"  - 이름: {site.get('product_name')}")
        print(f"  - 가격: {site.get('sale_product_fee', 0):,}원")
        print(f"  - 선택가능: {site.get('select_yn')}")
        print(f"  - 상태: {site.get('book_yn', 'N/A')}")

    print("\n" + "="*60)
    print("\n전체 좌석 데이터 (JSON):")
    print(json.dumps(sites, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
