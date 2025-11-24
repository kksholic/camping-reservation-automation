"""실시간 CAPTCHA 해결 및 예약 테스트"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.captcha_solver import get_captcha_solver
import requests
from dotenv import load_dotenv

load_dotenv()

SHOP_ENCODE = os.getenv('XTICKET_SHOP_ENCODE')
SHOP_CODE = os.getenv('XTICKET_SHOP_CODE')
USER_ID = os.getenv('XTICKET_USER_ID')
PASSWORD = os.getenv('XTICKET_PASSWORD')

BASE_URL = "https://camp.xticket.kr"

def test_captcha_and_reservation():
    """CAPTCHA 해결 및 예약 API 호출 테스트"""

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
    print("1. 메인 페이지 방문...")
    session.get(f"{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}")

    # 로그인
    print("2. 로그인 중...")
    login_url = f"{BASE_URL}/Web/Member/MemberLogin.json"
    login_data = {
        "member_id": USER_ID,
        "member_password": PASSWORD,
        "shopCode": SHOP_CODE
    }

    response = session.post(login_url, data=login_data)
    login_result = response.json()

    if not login_result.get('data', {}).get('success'):
        print(f"❌ 로그인 실패: {login_result}")
        return

    print(f"✅ 로그인 성공: {login_result['data'].get('member_id')}")

    # CAPTCHA 이미지 다운로드
    print("\n3. CAPTCHA 이미지 다운로드 중...")
    import random
    captcha_url = f"{BASE_URL}/Web/jcaptcha?r={random.random()}"

    captcha_response = session.get(captcha_url)
    captcha_image = captcha_response.content
    print(f"   CAPTCHA 이미지 크기: {len(captcha_image)} bytes")

    # CAPTCHA 해결
    print("\n4. EasyOCR로 CAPTCHA 해결 중...")
    print("   (첫 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다)")

    solver = get_captcha_solver()
    captcha_text = solver.solve_with_retry(captcha_image)

    if not captcha_text:
        print("❌ CAPTCHA 해결 실패")
        return

    print(f"✅ CAPTCHA 해결 성공: '{captcha_text}'")

    # 예약 API 호출 (테스트용 - 실제로 예약되지 않음)
    print(f"\n5. 예약 API 테스트 (product_code: 00040009)")

    reservation_url = f"{BASE_URL}/Web/Book/Book010001.json"
    reservation_data = {
        "product_group_code": "0004",
        "play_date": "20251121",
        "product_code": "00040009",
        "captcha": captcha_text
    }

    print(f"   요청 데이터: {reservation_data}")

    reservation_response = session.post(reservation_url, data=reservation_data)
    reservation_result = reservation_response.json()

    print(f"\n6. 예약 API 응답:")
    print(f"   {reservation_result}")

    if reservation_result.get('data', {}).get('success'):
        print(f"\n✅ 예약 성공!")
        print(f"   예약번호: {reservation_result['data'].get('reservation_number') or reservation_result['data'].get('book_no')}")
    else:
        print(f"\n⚠️  예약 실패 (예상된 결과일 수 있음)")
        print(f"   메시지: {reservation_result.get('data', {}).get('message', 'Unknown error')}")

if __name__ == "__main__":
    print("="*60)
    print("실시간 CAPTCHA 해결 및 예약 API 테스트")
    print("="*60)

    try:
        test_captcha_and_reservation()
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)
