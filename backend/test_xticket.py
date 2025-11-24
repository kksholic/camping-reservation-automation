"""XTicket 스크래퍼 독립 테스트 스크립트"""
import sys
import os

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

import requests
from datetime import datetime
import json


class XTicketScraper:
    """XTicket API 스크래퍼"""

    BASE_URL = "https://camp.xticket.kr"

    def __init__(self, shop_encode: str):
        self.shop_encode = shop_encode
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })
        # 세션 초기화 - 메인 페이지 방문하여 쿠키 받기
        self._init_session()

    def _init_session(self):
        """세션 초기화 - 메인 페이지 방문"""
        url = f"{self.BASE_URL}/web/main"
        params = {'shopEncode': self.shop_encode}

        print(f"🔄 세션 초기화 중... {url}")
        try:
            response = self.session.get(url, params=params)
            print(f"✅ 세션 초기화 완료 (상태: {response.status_code})")
            print(f"🍪 쿠키: {self.session.cookies.get_dict()}")
        except Exception as e:
            print(f"❌ 세션 초기화 실패: {e}")

    def get_available_dates(self, year: int, month: int):
        """예약 가능한 날짜 목록 조회"""
        url = f"{self.BASE_URL}/Web/Book/GetBookPlayDate.json"

        payload = {
            "shop_encode": self.shop_encode,
            "year": year,
            "month": month
        }

        print(f"\n📅 요청: {url}")
        print(f"📦 페이로드: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        try:
            # Content-Type을 application/json으로 명시
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(url, json=payload, headers=headers)
            print(f"✅ 응답 상태: {response.status_code}")

            data = response.json()
            print(f"📄 응답 데이터:\n{json.dumps(data, indent=2, ensure_ascii=False)}")

            return data

        except Exception as e:
            print(f"❌ 에러: {e}")
            return None

    def get_product_groups(self):
        """시설(상품) 그룹 조회"""
        url = f"{self.BASE_URL}/Web/Book/GetBookProductGroup.json"

        payload = {
            "shop_encode": self.shop_encode
        }

        print(f"\n🏕️ 요청: {url}")
        print(f"📦 페이로드: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        try:
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(url, json=payload, headers=headers)
            print(f"✅ 응답 상태: {response.status_code}")

            data = response.json()
            print(f"📄 응답 데이터:\n{json.dumps(data, indent=2, ensure_ascii=False)}")

            return data

        except Exception as e:
            print(f"❌ 에러: {e}")
            return None

    def get_shop_information(self):
        """캠핑장 기본 정보 조회"""
        url = f"{self.BASE_URL}/Web/Book/GetShopInformation.json"

        payload = {
            "shop_encode": self.shop_encode
        }

        print(f"\nℹ️ 요청: {url}")
        print(f"📦 페이로드: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        try:
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(url, json=payload, headers=headers)
            print(f"✅ 응답 상태: {response.status_code}")

            data = response.json()
            print(f"📄 응답 데이터:\n{json.dumps(data, indent=2, ensure_ascii=False)}")

            return data

        except Exception as e:
            print(f"❌ 에러: {e}")
            return None


def main():
    """테스트 실행"""
    print("=" * 60)
    print("🧪 XTicket API 스크래퍼 테스트")
    print("=" * 60)

    # 생림오토캠핑장 shop_encode
    SHOP_ENCODE = "f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940"

    scraper = XTicketScraper(SHOP_ENCODE)

    # 1. 캠핑장 정보 조회
    print("\n" + "=" * 60)
    print("TEST 1: 캠핑장 정보 조회")
    print("=" * 60)
    shop_info = scraper.get_shop_information()

    # 2. 예약 가능 날짜 조회 (2025년 11월)
    print("\n" + "=" * 60)
    print("TEST 2: 예약 가능 날짜 조회 (2025년 11월)")
    print("=" * 60)
    dates = scraper.get_available_dates(2025, 11)

    # 3. 시설 그룹 조회
    print("\n" + "=" * 60)
    print("TEST 3: 시설(상품) 그룹 조회")
    print("=" * 60)
    products = scraper.get_product_groups()

    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
