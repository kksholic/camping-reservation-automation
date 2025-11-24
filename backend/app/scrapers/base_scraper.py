"""베이스 스크래퍼 추상 클래스"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from playwright.sync_api import sync_playwright, Browser, Page
from loguru import logger


class BaseScraper(ABC):
    """모든 스크래퍼의 베이스 클래스"""

    def __init__(self):
        self.browser: Browser = None
        self.page: Page = None

    def init_browser(self, headless: bool = True):
        """브라우저 초기화"""
        logger.info(f"Initializing browser for {self.__class__.__name__}")

        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

        logger.info("Browser initialized")

    def close_browser(self):
        """브라우저 종료"""
        if self.browser:
            self.browser.close()
            logger.info("Browser closed")

    @abstractmethod
    def check_availability(self, url: str, target_date: str) -> bool:
        """
        예약 가능 여부 확인

        Args:
            url: 캠핑장 URL
            target_date: 확인할 날짜 (YYYY-MM-DD)

        Returns:
            예약 가능 여부 (True/False)
        """
        pass

    @abstractmethod
    def make_reservation(self, url: str, check_in: str, check_out: str,
                        user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        예약 실행

        Args:
            url: 캠핑장 URL
            check_in: 체크인 날짜 (YYYY-MM-DD)
            check_out: 체크아웃 날짜 (YYYY-MM-DD)
            user_info: 사용자 정보 (이름, 연락처 등)

        Returns:
            {
                'success': bool,
                'reservation_number': str,
                'error': str
            }
        """
        pass

    @abstractmethod
    def get_cancellation_info(self, url: str, target_date: str) -> list:
        """
        취소 정보 조회

        Args:
            url: 캠핑장 URL
            target_date: 확인할 날짜 (YYYY-MM-DD)

        Returns:
            취소된 예약 목록
        """
        pass

    def wait_for_element(self, selector: str, timeout: int = 10000):
        """엘리먼트 대기"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Element not found: {selector}, Error: {e}")
            return False

    def safe_click(self, selector: str):
        """안전한 클릭 (에러 처리)"""
        try:
            self.page.click(selector)
            return True
        except Exception as e:
            logger.error(f"Failed to click: {selector}, Error: {e}")
            return False

    def safe_fill(self, selector: str, value: str):
        """안전한 입력 (에러 처리)"""
        try:
            self.page.fill(selector, value)
            return True
        except Exception as e:
            logger.error(f"Failed to fill: {selector}, Error: {e}")
            return False
