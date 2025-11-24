# XTicket 스크래퍼 사용 가이드

## 개요

XTicket (camp.xticket.kr) 캠핑 예약 시스템을 위한 API 기반 스크래퍼입니다.

브라우저 자동화(Playwright) 대신 직접 HTTP API를 호출하여:
- ⚡ **더 빠른 속도** - 브라우저 오버헤드 없음
- 💪 **더 안정적** - 브라우저 크래시 없음
- 💰 **리소스 절약** - CPU/메모리 사용량 최소화

## 주요 API 엔드포인트

### 인증
- `POST /Web/Member/MemberLogin.json` - 로그인
- `POST /Web/Member/MemberLogout.json` - 로그아웃
- `POST /Web/Member/ChangePassword.json` - 비밀번호 변경

### 예약 조회
- `POST /Web/Book/GetBookPlayDate.json` - 예약 가능 날짜 조회
- `POST /Web/Book/GetBookProductGroup.json` - 시설 그룹 조회
- `POST /Web/Book/GetShopInformation.json` - 캠핑장 정보

### 예약 실행 (분석 필요)
- 실제 예약 API 엔드포인트는 추가 분석 필요
- 날짜 선택 후 "예매하기" 버튼 클릭 시 호출되는 API 확인 필요

## 사용 예제

### 1. 기본 사용법

```python
from app.scrapers.xticket_scraper import XTicketScraper

# 생림오토캠핑장 shop_encode
SHOP_ENCODE = "f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940"

# 스크래퍼 초기화
scraper = XTicketScraper(SHOP_ENCODE)

# 로그인
scraper.login("your_id", "your_password")

# 예약 가능 날짜 조회
dates = scraper.get_available_dates(2025, 11)
print(dates)

# 로그아웃
scraper.logout()
```

### 2. Context Manager 사용 (권장)

```python
with XTicketScraper(SHOP_ENCODE) as scraper:
    scraper.login("your_id", "your_password")

    # 예약 가능 날짜 조회
    dates = scraper.get_available_dates(2025, 11)

    # 특정 날짜 확인
    is_available = scraper.check_availability("2025-11-21")

    # 자동으로 로그아웃됨
```

### 3. 모니터링 서비스에 통합

```python
from app.scrapers.xticket_scraper import XTicketScraper

def monitor_xticket_site(shop_encode: str, target_date: str):
    """XTicket 사이트 모니터링"""

    with XTicketScraper(shop_encode) as scraper:
        # 로그인 (선택사항 - 비로그인 상태에서도 조회 가능)
        # scraper.login("id", "pw")

        # 예약 가능 여부 확인
        is_available = scraper.check_availability(target_date)

        return is_available
```

## Shop Encode 찾기

각 캠핑장마다 고유한 `shop_encode` 값이 있습니다.

URL에서 확인:
```
https://camp.xticket.kr/web/main?shopEncode=XXXXX
                                            ^^^^^^
                                            이 부분이 shop_encode
```

**예시:**
- 생림오토캠핑장: `f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940`

## TODO: 추가 분석 필요

### 1. 실제 예약 API
현재 예약 실행 API는 가정으로 구현되어 있습니다.
실제 예약 프로세스를 분석하여 정확한 엔드포인트와 파라미터 확인 필요:

1. 날짜 선택
2. 시설 선택
3. "예매하기" 버튼 클릭
4. 이 과정에서 호출되는 API 확인

### 2. API 응답 구조
각 API의 정확한 응답 구조 확인 필요:

```python
# 예상 구조 (실제 확인 필요)
{
    "success": true,
    "data": {
        "dates": [...],
        "products": [...]
    }
}
```

### 3. 세션/쿠키 관리
- 로그인 후 세션 유지 방법
- 쿠키 저장 및 재사용
- 세션 만료 처리

### 4. 에러 처리
- API 에러 코드 및 메시지
- 재시도 로직
- Rate limiting 대응

## 디버깅

실제 API 요청/응답을 확인하려면:

```python
import logging

# 로깅 활성화
logging.basicConfig(level=logging.DEBUG)

# requests 라이브러리 디버그 모드
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
```

또는 Chrome DevTools의 Network 탭에서:
1. 사이트 접속
2. F12 → Network 탭
3. 필요한 액션 수행
4. 호출된 API 확인

## 통합 방법

### MonitorService에 통합

`backend/app/services/monitor_service.py` 수정:

```python
from app.scrapers.xticket_scraper import XTicketScraper

class MonitorService:
    def __init__(self):
        self.scrapers = {
            'gocamp': GoCampScraper(),
            'naver': NaverScraper(),
            'xticket': XTicketScraper  # XTicket 추가
        }
```

### CampingSite 모델에 shop_encode 추가

```python
class CampingSite(db.Model):
    # ...
    site_config = db.Column(db.JSON)  # {'shop_encode': '...'} 저장
```

## 참고사항

- API 호출 간격: 최소 1초 이상 권장
- 동시 요청: 최대 3개 이하 권장
- 로그인: 필수가 아닐 수 있음 (날짜 조회는 비로그인 가능)
- 예약: 로그인 필수
