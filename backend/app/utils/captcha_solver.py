"""CAPTCHA 자동 해결 유틸리티 (PaddleOCR + EasyOCR 하이브리드)"""
import io
from typing import Optional
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from loguru import logger


class CaptchaSolver:
    """
    PaddleOCR + EasyOCR 하이브리드 CAPTCHA 자동 해결

    1차: PaddleOCR (빠름)
    2차: EasyOCR (fallback, 정확도 높음)
    """

    def __init__(self, lang_list: list = ['en']):
        """
        Args:
            lang_list: 인식할 언어 목록 (기본값: ['en'])
        """
        # PaddleOCR 초기화
        try:
            from paddleocr import PaddleOCR
            # PaddleOCR 3.x 버전은 간단한 파라미터만 사용
            self.paddle_ocr = PaddleOCR(lang='en')
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.warning(f"PaddleOCR initialization failed: {e}, will use EasyOCR only")
            self.paddle_ocr = None

        # EasyOCR 초기화 (fallback)
        try:
            import easyocr
            self.easy_reader = easyocr.Reader(lang_list, gpu=False)
            logger.info(f"EasyOCR initialized with languages: {lang_list}")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed: {e}")
            self.easy_reader = None

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        이미지 전처리로 인식률 향상

        Args:
            image: 원본 PIL Image

        Returns:
            전처리된 PIL Image
        """
        # 1. 흑백 변환
        image = image.convert('L')

        # 2. 대비 향상
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # 3. 선명도 향상
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)

        # 4. 노이즈 제거 (MedianFilter)
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # 5. 이진화 (Threshold)
        threshold = 128
        image = image.point(lambda p: 255 if p > threshold else 0)

        return image

    def _solve_with_paddle(self, image_np: np.ndarray) -> Optional[str]:
        """PaddleOCR로 CAPTCHA 해결"""
        if not self.paddle_ocr:
            return None

        try:
            result = self.paddle_ocr.ocr(image_np, cls=False)
            if result and result[0]:
                # PaddleOCR 결과 형식: [[[bbox], (text, confidence)], ...]
                texts = [line[1][0] for line in result[0]]
                text = ''.join(texts).strip()
                text = ''.join(c for c in text if c.isalnum())
                if text:
                    logger.info(f"PaddleOCR solved: {text}")
                    return text
        except Exception as e:
            logger.debug(f"PaddleOCR failed: {e}")

        return None

    def _solve_with_easy(self, image_np: np.ndarray) -> Optional[str]:
        """EasyOCR로 CAPTCHA 해결"""
        if not self.easy_reader:
            return None

        try:
            result = self.easy_reader.readtext(image_np, detail=0, paragraph=False)
            if result:
                text = ''.join(result).strip()
                text = ''.join(c for c in text if c.isalnum())
                if text:
                    logger.info(f"EasyOCR solved: {text}")
                    return text
        except Exception as e:
            logger.debug(f"EasyOCR failed: {e}")

        return None

    def solve(self, image_bytes: bytes, preprocess: bool = True) -> Optional[str]:
        """
        CAPTCHA 이미지에서 텍스트 추출 (하이브리드)

        Args:
            image_bytes: CAPTCHA 이미지 바이트 데이터
            preprocess: 이미지 전처리 여부 (기본값: True)

        Returns:
            추출된 텍스트 (실패 시 None)
        """
        try:
            # 이미지 로드
            image = Image.open(io.BytesIO(image_bytes))
            logger.debug(f"Loaded CAPTCHA image: {image.size}")

            # 전처리
            if preprocess:
                image = self.preprocess_image(image)
                logger.debug("Image preprocessing completed")

            # numpy array로 변환
            image_np = np.array(image)

            # 1차 시도: PaddleOCR (빠름)
            text = self._solve_with_paddle(image_np)
            if text:
                return text

            # 2차 시도: EasyOCR (정확도 높음)
            logger.debug("Falling back to EasyOCR...")
            text = self._solve_with_easy(image_np)
            if text:
                return text

            logger.warning("No text detected by any OCR engine")
            return None

        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return None

    def solve_with_retry(self, image_bytes: bytes, max_retries: int = 2) -> Optional[str]:
        """
        CAPTCHA 해결 재시도 (전처리 옵션 변경)

        Args:
            image_bytes: CAPTCHA 이미지 바이트 데이터
            max_retries: 최대 재시도 횟수

        Returns:
            추출된 텍스트 (실패 시 None)
        """
        # 첫 시도: 전처리 있음
        text = self.solve(image_bytes, preprocess=True)
        if text:
            return text

        # 재시도: 전처리 없음 (원본 이미지)
        if max_retries > 0:
            logger.info("Retrying CAPTCHA solving without preprocessing")
            text = self.solve(image_bytes, preprocess=False)
            if text:
                return text

        logger.error("CAPTCHA solving failed after all retries")
        return None


# 싱글톤 인스턴스
_captcha_solver = None


def get_captcha_solver() -> CaptchaSolver:
    """CAPTCHA Solver 싱글톤 인스턴스 반환"""
    global _captcha_solver
    if _captcha_solver is None:
        _captcha_solver = CaptchaSolver()
    return _captcha_solver


# 사용 예제
if __name__ == "__main__":
    import requests

    # 테스트용 CAPTCHA 이미지 URL (실제 사용 시 세션 필요)
    captcha_url = "https://camp.xticket.kr/Web/jcaptcha?r=0.12345"

    try:
        response = requests.get(captcha_url)
        solver = get_captcha_solver()

        text = solver.solve_with_retry(response.content)
        print(f"Solved CAPTCHA: {text}")

    except Exception as e:
        print(f"Error: {e}")
