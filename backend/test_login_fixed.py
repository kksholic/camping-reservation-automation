"""XTicket 로그인 수정 버전 - 브라우저와 동일하게"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import json
from load_credentials import get_xticket_credentials


def test_login_variations():
    """여러 방식으로 로그인 시도"""

    creds = get_xticket_credentials()
    SHOP_ENCODE = "f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940"
    BASE_URL = "https://camp.xticket.kr"

    print("=" * 60)
    print("🔬 로그인 방식 테스트")
    print("=" * 60)

    # 세션 초기화
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'X-Requested-With': 'XMLHttpRequest'
    })

    # 1. 세션 초기화
    print("\n[1] 세션 초기화")
    main_url = f"{BASE_URL}/web/main"
    params = {'shopEncode': SHOP_ENCODE}
    response = session.get(main_url, params=params)
    print(f"✅ 세션 초기화: {response.status_code}")
    print(f"🍪 쿠키: {list(session.cookies.keys())}")

    login_url = f"{BASE_URL}/Web/Member/MemberLogin.json"

    # 테스트 1: application/x-www-form-urlencoded (가장 일반적)
    print("\n" + "=" * 60)
    print("[TEST 1] application/x-www-form-urlencoded")
    print("=" * 60)

    data = {
        "user_id": creds['user_id'],
        "user_pw": creds['password'],
        "shop_encode": SHOP_ENCODE
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': f"{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}",
        'Origin': BASE_URL
    }

    response = session.post(login_url, data=data, headers=headers)
    print(f"상태 코드: {response.status_code}")
    print(f"응답 길이: {len(response.text)}")

    if response.status_code == 200:
        try:
            result = response.json()
            print(f"JSON 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")

            # 성공 판단
            if 'error' not in result:
                print("\n✅ 로그인 성공!")
                return True
        except:
            print(f"텍스트 응답: {response.text[:200]}")

    # 테스트 2: 다른 파라미터명 시도
    print("\n" + "=" * 60)
    print("[TEST 2] 파라미터명 변경 (id, pw)")
    print("=" * 60)

    data2 = {
        "id": creds['user_id'],
        "pw": creds['password'],
        "shop_encode": SHOP_ENCODE
    }

    response = session.post(login_url, data=data2, headers=headers)
    print(f"상태 코드: {response.status_code}")

    if response.status_code == 200:
        try:
            result = response.json()
            print(f"JSON 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")

            if 'error' not in result:
                print("\n✅ 로그인 성공!")
                return True
        except:
            print(f"텍스트 응답: {response.text[:200]}")

    # 테스트 3: JSON 형식 but with proper headers
    print("\n" + "=" * 60)
    print("[TEST 3] JSON + Referer + Origin")
    print("=" * 60)

    data3 = {
        "user_id": creds['user_id'],
        "user_pw": creds['password'],
        "shop_encode": SHOP_ENCODE
    }

    headers_json = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Referer': f"{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}",
        'Origin': BASE_URL
    }

    response = session.post(login_url, json=data3, headers=headers_json)
    print(f"상태 코드: {response.status_code}")

    if response.status_code == 200:
        try:
            result = response.json()
            print(f"JSON 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")

            if 'error' not in result:
                print("\n✅ 로그인 성공!")
                return True
        except:
            print(f"텍스트 응답: {response.text[:200]}")

    print("\n" + "=" * 60)
    print("❌ 모든 테스트 실패")
    print("=" * 60)
    return False


if __name__ == "__main__":
    test_login_variations()
