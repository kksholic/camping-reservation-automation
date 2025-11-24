"""직접 CAPTCHA 해결 테스트 (PaddleOCR + EasyOCR 하이브리드)"""
import io
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import requests
from dotenv import load_dotenv
import os

load_dotenv()

SHOP_ENCODE = os.getenv('XTICKET_SHOP_ENCODE')
SHOP_CODE = os.getenv('XTICKET_SHOP_CODE')
USER_ID = os.getenv('XTICKET_USER_ID')
PASSWORD = os.getenv('XTICKET_PASSWORD')

BASE_URL = "https://camp.xticket.kr"

def preprocess_image(image):
    """이미지 전처리"""
    # 흑백 변환
    image = image.convert('L')

    # 대비 향상
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # 선명도 향상
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)

    # 노이즈 제거
    image = image.filter(ImageFilter.MedianFilter(size=3))

    # 이진화
    threshold = 128
    image = image.point(lambda p: 255 if p > threshold else 0)

    return image

def solve_captcha(image_bytes):
    """CAPTCHA 해결 (PaddleOCR + EasyOCR 하이브리드)"""
    try:
        # 이미지 로드 및 전처리
        image = Image.open(io.BytesIO(image_bytes))
        image = preprocess_image(image)
        image_np = np.array(image)

        # 1차 시도: PaddleOCR (빠름)
        try:
            from paddleocr import PaddleOCR
            # PaddleOCR 3.x 버전 파라미터
            paddle_ocr = PaddleOCR(lang='en')
            result = paddle_ocr.ocr(image_np, cls=False)
            if result and result[0]:
                texts = [line[1][0] for line in result[0]]
                text = ''.join(texts).strip()
                text = ''.join(c for c in text if c.isalnum())
                if text:
                    print(f"   ✅ PaddleOCR로 해결: '{text}'")
                    return text
        except Exception as e:
            print(f"   ⚠️  PaddleOCR 실패, EasyOCR로 fallback... ({e})")

        # 2차 시도: EasyOCR (fallback)
        try:
            import easyocr
            reader = easyocr.Reader(['en'], gpu=False)
            result = reader.readtext(image_np, detail=0, paragraph=False)
            if result:
                text = ''.join(result).strip()
                text = ''.join(c for c in text if c.isalnum())
                if text:
                    print(f"   ✅ EasyOCR로 해결: '{text}'")
                    return text
        except Exception as e:
            print(f"   ❌ EasyOCR도 실패: {e}")

        return None
    except Exception as e:
        print(f"CAPTCHA 해결 오류: {e}")
        return None

def main():
    print("="*60)
    print("실시간 CAPTCHA 해결 및 예약 API 테스트 (하이브리드)")
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

    print(f"   ✅ 로그인 성공: {login_result['data'].get('member_id')}")

    # CAPTCHA 다운로드 및 해결
    print("\n3. CAPTCHA 다운로드 중...")
    import random
    captcha_url = f"{BASE_URL}/Web/jcaptcha?r={random.random()}"

    captcha_response = session.get(captcha_url)
    captcha_image = captcha_response.content
    print(f"   ✓ CAPTCHA 이미지 다운로드 완료 ({len(captcha_image)} bytes)")

    print("\n4. 하이브리드 OCR로 CAPTCHA 해결 중...")
    print("   (1차: PaddleOCR, 2차: EasyOCR)")

    captcha_text = solve_captcha(captcha_image)

    if not captcha_text:
        print("   ❌ CAPTCHA 해결 실패")
        return

    print(f"   ✅ CAPTCHA 해결 성공: '{captcha_text}'")
    print(f"      - 길이: {len(captcha_text)} 문자")

    # 예약 API 호출
    print(f"\n5. 예약 API 호출 (product_code: 00040009)")

    reservation_url = f"{BASE_URL}/Web/Book/Book010001.json"
    reservation_data = {
        "product_group_code": "0004",
        "play_date": "20251121",
        "product_code": "00040009",
        "captcha": captcha_text
    }

    print(f"   요청 데이터: {reservation_data}")

    # 드라이런 모드 체크
    dry_run = os.getenv('XTICKET_DRY_RUN', 'false').lower() == 'true'

    if dry_run:
        print(f"\n🧪 DRY RUN MODE - 실제 예약하지 않음")
        reservation_result = {
            "data": {
                "success": True,
                "book_no": "DRY_RUN_TEST",
                "message": "테스트 모드 - 실제 예약 안 함"
            }
        }
    else:
        reservation_response = session.post(reservation_url, data=reservation_data)
        reservation_result = reservation_response.json()

    print(f"\n6. 예약 API 응답:")
    import json
    print(json.dumps(reservation_result, indent=2, ensure_ascii=False))

    if reservation_result.get('data', {}).get('success'):
        print(f"\n✅✅✅ 예약 성공! ✅✅✅")
        print(f"   예약번호: {reservation_result['data'].get('reservation_number') or reservation_result['data'].get('book_no')}")
    else:
        error_msg = reservation_result.get('data', {}).get('message', 'Unknown error')
        print(f"\n⚠️  예약 실패")
        print(f"   메시지: {error_msg}")

        if 'captcha' in error_msg.lower() or '자동입력' in error_msg:
            print(f"   원인: CAPTCHA 인식 오류 - 재시도 필요")
        elif '선택' in error_msg or '상품' in error_msg:
            print(f"   원인: 사이트 선택 문제")
        else:
            print(f"   원인: 기타 오류")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)
