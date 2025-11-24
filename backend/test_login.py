"""XTicket 로그인 테스트"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import json
from load_credentials import get_xticket_credentials


class XTicketLoginTest:
    """XTicket 로그인 테스트"""

    BASE_URL = "https://camp.xticket.kr"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def init_session(self, shop_encode: str):
        """세션 초기화"""
        url = f"{self.BASE_URL}/web/main"
        params = {'shopEncode': shop_encode}

        print(f"🔄 세션 초기화 중...")
        response = self.session.get(url, params=params)
        print(f"✅ 세션 초기화 완료 (상태: {response.status_code})")
        print(f"🍪 쿠키: {list(self.session.cookies.keys())}")

    def login(self, shop_encode: str, user_id: str, password: str):
        """로그인 시도"""
        url = f"{self.BASE_URL}/Web/Member/MemberLogin.json"

        # Form data 형식으로 전송 (브라우저와 동일하게)
        data = {
            "user_id": user_id,
            "user_pw": password,
            "shop_encode": shop_encode
        }

        print(f"\n🔐 로그인 시도...")
        print(f"📦 요청 데이터:")
        print(f"   user_id: {user_id}")
        print(f"   user_pw: {'*' * len(password)}")
        print(f"   shop_encode: {shop_encode[:20]}...")

        try:
            # Form data로 전송 (application/x-www-form-urlencoded)
            response = self.session.post(url, data=data)

            print(f"\n✅ 응답 상태: {response.status_code}")

            # 응답 출력
            try:
                result = response.json()
                print(f"\n📄 응답 데이터:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return result
            except:
                print(f"\n📄 응답 내용 (텍스트):")
                print(response.text[:500])
                return None

        except Exception as e:
            print(f"\n❌ 에러 발생: {e}")
            return None


def main():
    """메인 테스트"""
    print("=" * 60)
    print("🧪 XTicket 로그인 테스트")
    print("=" * 60)

    # 1. .env에서 자격증명 로드
    print("\n[STEP 1] .env 파일에서 자격증명 로드")
    print("=" * 60)

    try:
        creds = get_xticket_credentials()
        print("✅ 자격증명 로드 성공!")
        print(f"\n사용자 ID: {creds['user_id']}")
        print(f"비밀번호: {'*' * len(creds['password'])}")
        print(f"이름: {creds['name']}")

        # 템플릿 기본값 체크
        if creds['user_id'] == 'your_xticket_id':
            print("\n⚠️  경고: .env 파일에 실제 값이 입력되지 않았습니다!")
            print("📝 .env 파일을 열어서 실제 XTicket 자격증명을 입력하세요.")
            print(f"\n파일 위치: backend\\.env")
            return

    except ValueError as e:
        print(f"❌ {e}")
        return

    # 2. 로그인 테스트
    print("\n[STEP 2] XTicket API 로그인 테스트")
    print("=" * 60)

    SHOP_ENCODE = "f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940"

    tester = XTicketLoginTest()

    # 세션 초기화
    tester.init_session(SHOP_ENCODE)

    # 로그인 시도
    result = tester.login(
        shop_encode=SHOP_ENCODE,
        user_id=creds['user_id'],
        password=creds['password']
    )

    # 결과 분석
    print("\n" + "=" * 60)
    print("📊 결과 분석")
    print("=" * 60)

    if result:
        # 에러 체크
        if 'error' in result:
            print(f"❌ 로그인 실패!")
            print(f"   에러 코드: {result['error'].get('code', 'N/A')}")
            print(f"   에러 메시지: {result['error'].get('message', 'N/A')}")
        elif 'success' in result or 'result' in result:
            print(f"✅ 로그인 성공!")
            print(f"   응답: {result}")
        else:
            print(f"⚠️  알 수 없는 응답:")
            print(f"   {result}")
    else:
        print(f"❌ 응답을 받지 못했습니다")

    print("=" * 60)


if __name__ == "__main__":
    main()
