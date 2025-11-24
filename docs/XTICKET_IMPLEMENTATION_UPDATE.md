# XTicket 스크래퍼 구현 업데이트

**작성일**: 2025-11-20
**상태**: 완료

---

## 작업 개요

API 분석 문서를 기반으로 `xticket_scraper.py` 코드를 실제 API 구조에 맞게 수정하고 테스트를 완료했습니다.

---

## 주요 수정 사항

### 1. 클래스 초기화 파라미터 변경

**이전:**
```python
def __init__(self, shop_encode: str):
```

**수정 후:**
```python
def __init__(self, shop_encode: str, shop_code: str):
```

**이유**:
- `shop_encode`: URL 파라미터용 (SHA-256 해시)
- `shop_code`: API 요청용 (숫자 코드)
- 두 값은 다르며 각각의 용도가 명확히 구분됨

---

### 2. 로그인 API 파라미터 수정

**이전:**
```python
payload = {
    "user_id": user_id,
    "user_pw": password,
    "shop_encode": self.shop_encode
}
```

**수정 후:**
```python
payload = {
    "member_id": user_id,
    "member_password": password,
    "shopCode": self.shop_code
}
```

**이유**: 실제 API 명세에 맞춰 파라미터 이름 변경

---

### 3. 세션 초기화 로직 추가

**새로 추가:**
```python
def _init_session(self):
    """세션 초기화 - 메인 페이지 방문하여 쿠키 획득"""
    try:
        main_url = f"{self.BASE_URL}/web/main?shopEncode={self.shop_encode}"
        self.session.get(main_url)
        logger.debug("Session initialized by visiting main page")
    except Exception as e:
        logger.warning(f"Failed to initialize session: {e}")
```

**이유**: XTicket은 로그인 전 메인 페이지 방문 필수 (Referer 검증 및 세션 쿠키 획득)

---

### 4. 예약 가능 날짜 조회 API 수정

**이전:**
```python
payload = {
    "play_month": play_month,
    "shop_encode": self.shop_encode
}
```

**수정 후:**
```python
payload = {
    "play_month": play_month
}
```

**이유**: 실제 API는 `play_month` 파라미터만 필요

---

### 5. 시설 그룹 조회 API 수정

**이전:**
```python
def get_product_groups(self) -> list:
    payload = {
        "shop_encode": self.shop_encode
    }
```

**수정 후:**
```python
def get_product_groups(self, start_date: str, end_date: str) -> list:
    payload = {
        "start_date": start_date,
        "end_date": end_date
    }
```

**이유**:
- 실제 API는 `start_date`, `end_date` 필수 파라미터 요구
- 응답 구조는 `bookProductGroupList` 키 사용

---

### 6. 환경 변수 추가

**`.env` 파일에 추가:**
```bash
XTICKET_SHOP_ENCODE=f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940
XTICKET_SHOP_CODE=622830018001
```

**`.env.example` 파일에도 동일하게 추가**

---

## 테스트 결과

### 테스트 스크립트 작성
- 파일: `backend/test_xticket_simple.py`
- Flask 종속성 없이 단독 실행 가능한 테스트 스크립트

### 테스트 성공 확인

```
✅ 로그인 성공: rltjd0627
   회원번호: 713632

✅ 캠핑장 이름: 생림오토캠핑장
   예약 가능 일수: 31일
   1일 예약 사이트 수: 1개
   결제 방법: CARD,VBANK

✅ 총 6개 날짜 조회됨
   예약 가능: 4개
   예약 불가: 2개
   예약 가능한 날짜:
   - 2025-11-21: 잔여 50개
   - 2025-11-23: 잔여 105개
   - 2025-11-28: 잔여 48개
   - 2025-11-30: 잔여 108개

✅ 총 3개 시설 그룹 조회됨
   [0001] 잔디사이트 - 요금: 30,000원
   [0002] 데크사이트 - 요금: 30,000원
   [0004] 파쇄석사이트 - 요금: 30,000원
```

---

## 검증된 기능

### ✅ 구현 완료
1. **로그인**: 정상 작동 (세션 초기화 포함)
2. **캠핑장 정보 조회**: 정상 작동
3. **예약 가능 날짜 조회**: 정상 작동
4. **시설 그룹 조회**: 정상 작동
5. **특정 날짜 예약 가능 여부 확인**: 정상 작동

### ⚠️ 미구현 (추가 분석 필요)
1. **예약 실행 API** - 실제 예약 버튼 클릭 시 네트워크 분석 필요
2. **예약 취소 API** - 취소 프로세스 분석 필요
3. **예약 내역 조회 API** - "예약내역(결제/취소)" 페이지 분석 필요
4. **결제 API** - PG 연동 방식 확인 필요

---

## 사용 예제

### 기본 사용법

```python
from app.scrapers.xticket_scraper import XTicketScraper
import os

# 환경 변수에서 설정 읽기
SHOP_ENCODE = os.getenv('XTICKET_SHOP_ENCODE')
SHOP_CODE = os.getenv('XTICKET_SHOP_CODE')
USER_ID = os.getenv('XTICKET_USER_ID')
PASSWORD = os.getenv('XTICKET_PASSWORD')

# 스크래퍼 사용
with XTicketScraper(SHOP_ENCODE, SHOP_CODE) as scraper:
    # 로그인
    if scraper.login(USER_ID, PASSWORD):
        # 예약 가능 날짜 조회
        dates = scraper.get_available_dates(2025, 11)

        # 시설 목록 조회
        products = scraper.get_product_groups("20251101", "20251131")

        # 특정 날짜 확인
        is_available = scraper.check_availability("2025-11-21")
```

---

## 중요 발견 사항

### 1. 세션 관리의 중요성
- XTicket은 로그인 전 반드시 메인 페이지 방문 필요
- 쿠키 기반 세션 관리 필수
- Referer 헤더 검증 엄격

### 2. 파라미터 인코딩
- Content-Type: `application/x-www-form-urlencoded; charset=UTF-8` 필수
- JSON으로 전송 시 "세션 만료" 오류 발생

### 3. 응답 구조 일관성
- 모든 API 응답은 `{data: {...}}` 래퍼 구조 사용
- 성공 여부는 `data.success` 필드로 확인

### 4. 날짜 형식
- 요청/응답 모두 `YYYYMMDD` 형식 사용 (예: "20251121")

---

## 다음 단계

### 우선순위 높음
1. **예약 실행 API 분석**
   - 실제 예약 프로세스 네트워크 분석
   - 필요한 파라미터 및 검증 로직 확인
   - `make_reservation()` 메서드 구현

2. **에러 핸들링 강화**
   - API 응답 상태 코드별 처리
   - 재시도 로직 추가
   - 타임아웃 설정

### 우선순위 중간
1. **예약 취소 API 분석 및 구현**
2. **예약 내역 조회 API 분석 및 구현**
3. **통합 테스트 케이스 작성**

### 우선순위 낮음
1. **결제 API 연동** (수동 결제로 대체 가능)
2. **알림 기능 통합**
3. **로깅 강화**

---

## 참고 자료

- [XTICKET_API_ANALYSIS.md](./XTICKET_API_ANALYSIS.md) - API 상세 분석 문서
- [test_xticket_simple.py](../backend/test_xticket_simple.py) - 테스트 스크립트

---

**문서 끝**
