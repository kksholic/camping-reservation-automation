"""CAPTCHA 해결 테스트 스크립트"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.utils.captcha_solver import get_captcha_solver
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수
SHOP_ENCODE = os.getenv('XTICKET_SHOP_ENCODE')
USER_ID = os.getenv('XTICKET_USER_ID')
PASSWORD = os.getenv('XTICKET_PASSWORD')

BASE_URL = "https://camp.xticket.kr"


def test_captcha_solving():
    """CAPTCHA 해결 테스트"""
    print("\n" + "="*60)
    print("CAPTCHA 해결 테스트")
    print("="*60)

    # 세션 생성 및 로그인
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })

    # 메인 페이지 방문
    print("\n[1] 메인 페이지 방문 중...")
    main_url = f"{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}"
    session.get(main_url)
    print("   ✓ 세션 생성 완료")

    # CAPTCHA 이미지 다운로드
    print("\n[2] CAPTCHA 이미지 다운로드 중...")
    captcha_url = f"{BASE_URL}/Web/jcaptcha?r=0.12345"

    try:
        response = session.get(captcha_url)
        response.raise_for_status()

        captcha_image = response.content
        print(f"   ✓ CAPTCHA 이미지 다운로드 완료 ({len(captcha_image)} bytes)")

        # CAPTCHA 해결
        print("\n[3] EasyOCR로 CAPTCHA 해결 중...")
        solver = get_captcha_solver()

        captcha_text = solver.solve_with_retry(captcha_image)

        if captcha_text:
            print(f"   ✅ CAPTCHA 해결 성공: '{captcha_text}'")
            print(f"   - 길이: {len(captcha_text)} 문자")
            print(f"   - 타입: {'숫자' if captcha_text.isdigit() else '영문' if captcha_text.isalpha() else '혼합'}")
        else:
            print("   ❌ CAPTCHA 해결 실패")

        return captcha_text

    except Exception as e:
        print(f"   ❌ 에러: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n⚠️  참고: EasyOCR 첫 실행 시 모델을 다운로드하므로 시간이 걸릴 수 있습니다.\n")

    captcha_text = test_captcha_solving()

    print("\n" + "="*60)
    if captcha_text:
        print("테스트 성공!")
        print(f"해결된 CAPTCHA: {captcha_text}")
    else:
        print("테스트 실패 - CAPTCHA를 해결할 수 없습니다.")
    print("="*60 + "\n")
