"""XTicket 캠핑 예약 시스템 스크래퍼 (API 기반)"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import requests
import time
from email.utils import parsedate_to_datetime


class XTicketScraper:
    """
    XTicket (camp.xticket.kr) API 기반 스크래퍼

    브라우저 자동화 대신 직접 API를 호출하여 더 빠르고 안정적으로 동작
    """

    BASE_URL = "https://camp.xticket.kr"

    def __init__(self, shop_encode: str, shop_code: str, max_retries: int = 3,
                 retry_delay: float = 1.0, timeout: int = 30):
        """
        Args:
            shop_encode: 캠핑장 고유 코드 (URL의 shopEncode 파라미터)
            shop_code: 캠핑장 코드 (API 요청용)
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간 기본 대기 시간 (초)
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.shop_encode = shop_encode
        self.shop_code = shop_code
        self.session = requests.Session()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.server_time_offset = None  # 서버-로컬 시간 차이 (초)

        # 실제 API 요청에 맞는 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.BASE_URL}/web/main?shopEncode={shop_encode}',
            'Origin': self.BASE_URL
        })
        self.is_logged_in = False

    def _make_request_with_retry(self, method: str, url: str, **kwargs):
        """
        재시도 로직이 적용된 HTTP 요청 (exponential backoff)

        Args:
            method: HTTP 메서드 ('GET', 'POST')
            url: 요청 URL
            **kwargs: requests 메서드 인자

        Returns:
            requests.Response

        Raises:
            requests.RequestException: 모든 재시도 실패 시
        """
        kwargs.setdefault('timeout', self.timeout)

        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()
                return response

            except (requests.Timeout, requests.ConnectionError) as e:
                # 타임아웃 또는 연결 오류는 재시도
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise

            except requests.HTTPError as e:
                # HTTP 에러 (4xx, 5xx)는 서버 측 문제일 수 있으므로 재시도
                if e.response.status_code >= 500:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error {e.response.status_code} (attempt {attempt + 1}/{self.max_retries})")

                    if attempt < self.max_retries - 1:
                        logger.info(f"Retrying in {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise
                else:
                    # 4xx 에러는 재시도하지 않음
                    raise

    def get_server_time(self) -> Optional[datetime]:
        """
        XTicket 서버 시간 가져오기 (HTTP Date 헤더 사용)

        Returns:
            서버 시간 (datetime 객체) 또는 None
        """
        try:
            # 실제 캠핑장 페이지 URL 사용 (BASE_URL은 404 반환)
            main_url = f"{self.BASE_URL}/web/main?shopEncode={self.shop_encode}"
            response = self._make_request_with_retry('GET', main_url)

            # HTTP Date 헤더 파싱
            date_header = response.headers.get('Date')
            if date_header:
                server_time = parsedate_to_datetime(date_header)
                logger.info(f"Server time: {server_time.isoformat()}")
                return server_time
            else:
                logger.warning("No Date header in response")
                return None

        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            return None

    def sync_server_time(self) -> bool:
        """
        서버 시간과 로컬 시간 동기화 (오프셋 계산)

        Returns:
            동기화 성공 여부
        """
        try:
            from datetime import timezone
            local_time_before = datetime.now(timezone.utc)
            server_time = self.get_server_time()
            local_time_after = datetime.now(timezone.utc)

            if not server_time:
                return False

            # 로컬 시간은 요청 전후 평균값 사용
            local_time_avg = local_time_before + (local_time_after - local_time_before) / 2

            # 오프셋 계산 (서버 시간 - 로컬 시간)
            self.server_time_offset = (server_time - local_time_avg).total_seconds()

            logger.info(f"Server time offset: {self.server_time_offset:.2f} seconds")
            logger.info(f"Local: {local_time_avg.isoformat()} -> Server: {server_time.isoformat()}")

            return True

        except Exception as e:
            logger.error(f"Failed to sync server time: {e}")
            return False

    def get_adjusted_local_time(self) -> datetime:
        """
        서버 시간에 맞춰 조정된 로컬 시간 반환

        Returns:
            조정된 현재 시간 (서버 시간 기준)
        """
        local_time = datetime.utcnow()

        if self.server_time_offset is not None:
            adjusted_time = local_time + timedelta(seconds=self.server_time_offset)
            return adjusted_time
        else:
            logger.warning("Server time not synced, using local time")
            return local_time

    def _init_session(self):
        """세션 초기화 - 메인 페이지 방문하여 쿠키 획득 및 서버 시간 동기화"""
        try:
            main_url = f"{self.BASE_URL}/web/main?shopEncode={self.shop_encode}"
            self.session.get(main_url, timeout=self.timeout)
            logger.debug("Session initialized by visiting main page")

            # 서버 시간 동기화
            self.sync_server_time()

        except Exception as e:
            logger.warning(f"Failed to initialize session: {e}")

    def login(self, user_id: str, password: str) -> bool:
        """
        로그인

        Args:
            user_id: 사용자 아이디
            password: 비밀번호

        Returns:
            로그인 성공 여부
        """
        # 먼저 메인 페이지 방문하여 세션 초기화
        self._init_session()

        url = f"{self.BASE_URL}/Web/Member/MemberLogin.json"

        payload = {
            "member_id": user_id,
            "member_password": password,
            "shopCode": self.shop_code
        }

        try:
            response = self._make_request_with_retry('POST', url, data=payload)
            data = response.json()

            # 응답 구조: {data: {success: true, member_id: ..., member_no: ...}}
            if data.get('data', {}).get('success'):
                self.is_logged_in = True
                logger.info(f"Login successful for user: {user_id}")
                return True
            else:
                error_msg = data.get('data', {}).get('message', 'Login failed')
                logger.error(f"Login failed: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def logout(self) -> bool:
        """로그아웃"""
        url = f"{self.BASE_URL}/Web/Member/MemberLogout.json"

        try:
            response = self.session.post(url)
            response.raise_for_status()
            self.is_logged_in = False
            logger.info("Logout successful")
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    def _get_dry_run_setting(self) -> bool:
        """
        DRY_RUN 설정 가져오기 - DB 설정 우선, 환경 변수는 fallback

        Returns:
            bool: DRY_RUN 모드 여부
        """
        import os
        try:
            # Flask 앱 컨텍스트 필요
            from flask import current_app
            if current_app:
                from app.models.database import AppSettings
                settings = AppSettings.query.first()
                if settings and settings.xticket_dry_run is not None:
                    logger.debug(f"Using DRY_RUN from database: {settings.xticket_dry_run}")
                    return settings.xticket_dry_run
        except Exception as e:
            # 앱 컨텍스트 없거나 DB 조회 실패 시 무시
            logger.debug(f"Failed to get DRY_RUN from DB: {e}")

        # Fallback: 환경 변수
        env_dry_run = os.getenv('XTICKET_DRY_RUN', 'false').lower() == 'true'
        logger.debug(f"Using DRY_RUN from environment: {env_dry_run}")
        return env_dry_run

    def get_available_dates(self, year: int, month: int) -> list:
        """
        예약 가능한 날짜 목록 조회

        Args:
            year: 연도 (예: 2025)
            month: 월 (1-12)

        Returns:
            예약 가능한 날짜 목록 [{'date': '2025-11-21', 'available': True, 'remain_count': 5}, ...]
        """
        url = f"{self.BASE_URL}/Web/Book/GetBookPlayDate.json"

        # 실제 API는 play_month 형태로 전달 (예: "202511")
        play_month = f"{year}{month:02d}"

        payload = {
            "play_month": play_month
        }

        try:
            response = self.session.post(url, data=payload)
            response.raise_for_status()

            data = response.json()

            # 실제 응답 구조: {data: {bookPlayDateList: [...]}}
            dates = []

            if 'data' in data and 'bookPlayDateList' in data['data']:
                for date_info in data['data']['bookPlayDateList']:
                    # play_date 형태: "20251121"
                    play_date = date_info.get('play_date', '')
                    if play_date and len(play_date) == 8:
                        formatted_date = f"{play_date[:4]}-{play_date[4:6]}-{play_date[6:8]}"
                        remain_count = date_info.get('book_remain_count', 0)

                        dates.append({
                            'date': formatted_date,
                            'available': remain_count > 0,
                            'remain_count': remain_count,
                            'status': 'available' if remain_count > 0 else 'unavailable'
                        })

            logger.info(f"Found {len(dates)} dates for {year}-{month:02d}")
            return dates

        except Exception as e:
            logger.error(f"Error fetching available dates: {e}")
            return []

    def get_product_groups(self, start_date: str, end_date: str) -> list:
        """
        시설(상품) 그룹 조회

        Args:
            start_date: 시작 날짜 (YYYYMMDD 형식, 예: "20251101")
            end_date: 종료 날짜 (YYYYMMDD 형식, 예: "20251131")

        Returns:
            시설 목록 [{'product_group_code': '0001', 'product_group_name': '잔디사이트', ...}, ...]
        """
        url = f"{self.BASE_URL}/Web/Book/GetBookProductGroup.json"

        payload = {
            "start_date": start_date,
            "end_date": end_date
        }

        try:
            response = self.session.post(url, data=payload)
            response.raise_for_status()

            data = response.json()

            # 실제 응답 구조: {data: {bookProductGroupList: [...]}}
            products = []

            if 'data' in data and 'bookProductGroupList' in data['data']:
                products = data['data']['bookProductGroupList']

            logger.info(f"Found {len(products)} product groups")
            return products

        except Exception as e:
            logger.error(f"Error fetching product groups: {e}")
            return []

    def get_available_sites(self, target_date: str, product_group_code: str = "0004",
                           book_days: int = 1) -> list:
        """
        특정 날짜의 선택 가능한 개별 사이트 조회

        Args:
            target_date: 확인할 날짜 (YYYY-MM-DD 또는 YYYYMMDD)
            product_group_code: 시설 그룹 코드 (기본값: "0004" 파쇄석사이트)
            book_days: 숙박 일수 (1박2일 = 1, 2박3일 = 2)

        Returns:
            선택 가능한 사이트 목록 [
                {
                    'product_code': '00040009',
                    'product_name': '금관-09',
                    'select_yn': '1',
                    'sale_product_fee': 30000,
                    ...
                },
                ...
            ]
        """
        url = f"{self.BASE_URL}/Web/Book/GetBookProduct010001.json"

        # 날짜 형식 정규화 (YYYY-MM-DD -> YYYYMMDD)
        date_str = target_date.replace('-', '')

        payload = {
            "product_group_code": product_group_code,
            "start_date": date_str,
            "end_date": date_str,
            "book_days": book_days,
            "two_stay_days": 0,
            "shopCode": self.shop_code
        }

        try:
            response = self.session.post(url, data=payload)
            response.raise_for_status()

            data = response.json()

            # 실제 응답 구조: {data: {bookProductList: [...]}}
            all_sites = data.get('data', {}).get('bookProductList', [])

            # 선택 가능한 사이트만 필터링 (select_yn == "1" 또는 sale_product_fee > 0)
            available_sites = [
                site for site in all_sites
                if site.get('select_yn') == '1' or site.get('sale_product_fee', 0) > 0
            ]

            logger.info(f"Found {len(available_sites)} available sites on {target_date} "
                       f"(total: {len(all_sites)})")

            return available_sites

        except Exception as e:
            logger.error(f"Error fetching available sites: {e}")
            return []

    def get_shop_information(self) -> Dict[str, Any]:
        """
        캠핑장 기본 정보 조회

        Returns:
            캠핑장 정보 딕셔너리
        """
        url = f"{self.BASE_URL}/Web/Book/GetShopInformation.json"

        payload = {
            "shop_encode": self.shop_encode
        }

        try:
            response = self.session.post(url, data=payload)
            response.raise_for_status()

            data = response.json()

            # 실제 응답: {data: {...}}
            shop_info = data.get('data', {})

            logger.info(f"Shop information retrieved: {shop_info.get('shop_name', 'Unknown')}")
            return shop_info

        except Exception as e:
            logger.error(f"Error fetching shop information: {e}")
            return {}

    def check_availability(self, target_date: str, product_id: Optional[int] = None) -> bool:
        """
        특정 날짜의 예약 가능 여부 확인

        Args:
            target_date: 확인할 날짜 (YYYY-MM-DD)
            product_id: 시설 ID (선택사항)

        Returns:
            예약 가능 여부
        """
        try:
            # 날짜 파싱
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            year = date_obj.year
            month = date_obj.month

            # 해당 월의 예약 가능 날짜 조회
            available_dates = self.get_available_dates(year, month)

            # 특정 날짜 확인
            for date_info in available_dates:
                if date_info['date'] == target_date:
                    is_available = date_info['available']
                    logger.info(f"Date {target_date} availability: {is_available} (remain: {date_info['remain_count']})")
                    return is_available

            logger.warning(f"Date {target_date} not found in available dates")
            return False

        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False

    def _solve_captcha(self, captcha_image_url: str) -> Optional[str]:
        """
        CAPTCHA 이미지 해결

        Args:
            captcha_image_url: CAPTCHA 이미지 URL

        Returns:
            해결된 CAPTCHA 텍스트 (실패 시 None)
        """
        try:
            from app.utils.captcha_solver import get_captcha_solver

            # CAPTCHA 이미지 다운로드
            response = self.session.get(captcha_image_url)
            response.raise_for_status()

            # OCR로 CAPTCHA 해결
            solver = get_captcha_solver()
            captcha_text = solver.solve_with_retry(response.content)

            if captcha_text:
                logger.info(f"CAPTCHA solved: {captcha_text}")
                return captcha_text
            else:
                logger.error("Failed to solve CAPTCHA")
                return None

        except Exception as e:
            logger.error(f"CAPTCHA solving error: {e}")
            return None

    def make_reservation(self, target_date: str, product_codes: list,
                        product_group_code: str = "0004",
                        book_days: int = 1,
                        dry_run: bool = None) -> Dict[str, Any]:
        """
        예약 실행 (우선순위 기반)

        Args:
            target_date: 체크인 날짜 (YYYY-MM-DD)
            product_codes: 우선순위 순서대로 정렬된 사이트 코드 목록 (예: ['00040009', '00040010', '00040012'])
            product_group_code: 시설 그룹 코드 (기본값: "0004" 파쇄석사이트)
            book_days: 숙박 일수 (1박2일 = 1, 2박3일 = 2)

        Returns:
            {
                'success': bool,
                'reservation_number': str,
                'selected_site': str,
                'error': str
            }
        """
        if not self.is_logged_in:
            return {
                'success': False,
                'error': 'Not logged in'
            }

        url = f"{self.BASE_URL}/Web/Book/Book010001.json"

        # 날짜 형식 변환 (YYYY-MM-DD -> YYYYMMDD)
        date_str = target_date.replace('-', '')

        # play_date 생성 (1박2일이면 1개 날짜, 2박3일이면 2개 날짜)
        from datetime import datetime, timedelta
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        play_dates = []
        for i in range(book_days):
            next_date = date_obj + timedelta(days=i)
            play_dates.append(next_date.strftime('%Y%m%d'))
        play_date = ','.join(play_dates)

        import random
        import os

        # 드라이런 모드 체크
        # 1. 함수 인자로 전달된 값 (스케줄 설정)
        # 2. DB 설정
        # 3. 환경 변수 fallback
        if dry_run is None:
            dry_run = self._get_dry_run_setting()

        # CAPTCHA 최대 재시도 횟수
        max_captcha_retries = 10

        # 우선순위 순서대로 사이트 시도
        for product_code in product_codes:
            logger.info(f"Attempting reservation for site: {product_code}")

            captcha_retries = 0

            # 같은 좌석에 대해 CAPTCHA 재시도
            while captcha_retries < max_captcha_retries:
                # CAPTCHA 이미지 URL 생성
                captcha_url = f"{self.BASE_URL}/Web/jcaptcha?r={random.random()}"

                # CAPTCHA 해결
                captcha_text = self._solve_captcha(captcha_url)
                if not captcha_text:
                    captcha_retries += 1
                    logger.warning(f"Failed to solve CAPTCHA (attempt {captcha_retries}/{max_captcha_retries})")
                    if captcha_retries >= max_captcha_retries:
                        logger.warning(f"Max CAPTCHA solve failures for {product_code}, trying next site")
                        break
                    continue

                # 예약 요청
                payload = {
                    "product_group_code": product_group_code,
                    "play_date": play_date,
                    "product_code": product_code,
                    "captcha": captcha_text
                }

                if dry_run:
                    logger.info("🧪 DRY RUN MODE - 실제 예약하지 않음")
                    logger.info(f"예약 시뮬레이션: {payload}")
                    return {
                        'success': True,
                        'reservation_number': 'DRY_RUN_TEST',
                        'selected_site': product_code,
                        'target_date': target_date,
                        'dry_run': True
                    }

                try:
                    response = self.session.post(url, data=payload)
                    response.raise_for_status()

                    data = response.json()

                    # 응답 구조 확인:
                    # 성공: {data: {success: true, book_no: ...}}
                    # 실패: {error: {message: ..., code: ...}}
                    if 'error' in data:
                        error_info = data.get('error', {})
                        error_msg = error_info.get('message', 'Unknown error')
                        logger.warning(f"Reservation failed for {product_code}: {error_msg}")

                        # CAPTCHA 오류면 같은 좌석 재시도
                        if 'captcha' in error_msg.lower() or '자동입력' in error_msg:
                            captcha_retries += 1
                            logger.info(f"CAPTCHA error (attempt {captcha_retries}/{max_captcha_retries}), retrying same site")
                            if captcha_retries < max_captcha_retries:
                                continue  # 같은 좌석 재시도 (내부 while 루프)
                            else:
                                logger.warning(f"Max CAPTCHA retries reached for {product_code}, trying next site")
                                break  # 다음 좌석으로
                        else:
                            # 좌석 없음 등 다른 오류 - 다음 좌석 시도
                            logger.info(f"Site {product_code} unavailable, trying next priority site")
                            break  # 다음 좌석으로

                    elif 'data' in data:
                        result_data = data.get('data', {})
                        if result_data.get('success'):
                            reservation_number = result_data.get('reservation_number') or result_data.get('book_no')
                            logger.info(f"Reservation successful: {reservation_number} for site {product_code}")
                            return {
                                'success': True,
                                'reservation_number': reservation_number,
                                'selected_site': product_code,
                                'target_date': target_date
                            }
                        else:
                            error_msg = result_data.get('message', 'Reservation failed')
                            logger.warning(f"Reservation failed for {product_code}: {error_msg}")
                            break  # 다음 좌석으로
                    else:
                        logger.warning(f"Unknown response format: {data}")
                        break  # 다음 좌석으로

                except Exception as e:
                    logger.error(f"Reservation error for {product_code}: {e}")
                    break  # 다음 좌석으로

        # 모든 우선순위 사이트에서 실패
        return {
            'success': False,
            'error': 'All priority sites failed - either unavailable or CAPTCHA issues',
            'attempted_sites': product_codes
        }

    def get_cancellation_info(self, target_date: str) -> list:
        """
        취소 정보 조회

        Args:
            target_date: 확인할 날짜 (YYYY-MM-DD)

        Returns:
            취소된 예약 목록
        """
        # 취소 정보 API는 별도 분석 필요
        # 현재는 예약 가능 날짜 조회를 통해 간접적으로 파악
        logger.info(f"Checking cancellation info for {target_date}")

        is_available = self.check_availability(target_date)

        if is_available:
            return [{
                'date': target_date,
                'status': 'available_after_cancellation'
            }]

        return []

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료 시 로그아웃"""
        if self.is_logged_in:
            self.logout()


# 사용 예제
if __name__ == "__main__":
    # 생림오토캠핑장 정보
    SHOP_ENCODE = "f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940"
    SHOP_CODE = "622830018001"

    # Context manager 사용
    with XTicketScraper(SHOP_ENCODE, SHOP_CODE) as scraper:
        # 1. 로그인
        # success = scraper.login("your_id", "your_password")

        # 2. 예약 가능 날짜 조회
        dates = scraper.get_available_dates(2025, 11)
        print(f"Available dates: {dates}")

        # 3. 시설 목록 조회
        products = scraper.get_product_groups("20251101", "20251131")
        print(f"Products: {products}")

        # 4. 캠핑장 정보 조회
        shop_info = scraper.get_shop_information()
        print(f"Shop info: {shop_info}")

        # 5. 특정 날짜 예약 가능 여부 확인
        is_available = scraper.check_availability("2025-11-21")
        print(f"2025-11-21 available: {is_available}")
