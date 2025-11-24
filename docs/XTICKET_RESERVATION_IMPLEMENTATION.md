# XTicket 예약 시스템 구현 완료

**작성일**: 2025-11-20
**상태**: 완료

---

## 구현 개요

XTicket 캠핑 예약 시스템의 **우선순위 기반 자동 예약 기능**을 완성했습니다.

---

## 핵심 기능

### 1. **우선순위 기반 예약**
- 사용자가 선호하는 사이트를 우선순위 순서로 지정
- 1순위 사이트부터 순서대로 예약 시도
- 한 사이트 실패 시 자동으로 다음 우선순위 사이트로 이동

### 2. **CAPTCHA 자동 해결**
- EasyOCR을 사용한 자동 인식
- 이미지 전처리로 인식률 향상 (흑백 변환, 대비 강화, 노이즈 제거)
- 실패 시 재시도 로직

### 3. **실시간 사이트 가용성 확인**
- `get_available_sites()` 메서드로 특정 날짜의 예약 가능한 사이트 조회
- `select_yn == "1"` 필드로 선택 가능 여부 판단

---

## API 엔드포인트

### 예약 실행 API
**URL**: `/Web/Book/Book010001.json`
**Method**: POST
**Parameters**:
```json
{
  "product_group_code": "0004",       // 시설 그룹 코드 (파쇄석사이트)
  "play_date": "20251121",            // 체크인 날짜 (1박2일)
  "product_code": "00040009",         // 사이트 코드
  "captcha": "abc123"                 // CAPTCHA 텍스트
}
```

**Response**:
```json
{
  "data": {
    "success": true,
    "reservation_number": "R20251121001",
    "book_no": "R20251121001"
  }
}
```

### 개별 사이트 조회 API
**URL**: `/Web/Book/GetBookProduct010001.json`
**Method**: POST
**Parameters**:
```json
{
  "product_group_code": "0004",
  "start_date": "20251121",
  "end_date": "20251121",
  "book_days": 1,
  "two_stay_days": 0,
  "shopCode": "622830018001"
}
```

---

## 구현된 메서드

### `get_available_sites()`
특정 날짜의 예약 가능한 개별 사이트 목록 조회

```python
available_sites = scraper.get_available_sites(
    target_date="2025-11-21",
    product_group_code="0004",  # 파쇄석사이트
    book_days=1                  # 1박2일
)

# 반환 예시:
# [
#   {'product_code': '00040009', 'product_name': '금관-09', 'select_yn': '1', ...},
#   {'product_code': '00040010', 'product_name': '금관-10', 'select_yn': '1', ...},
#   ...
# ]
```

### `make_reservation()`
우선순위 기반 자동 예약 실행

```python
result = scraper.make_reservation(
    target_date="2025-11-21",
    product_codes=['00040009', '00040010', '00040012'],  # 우선순위 순서
    product_group_code="0004",
    book_days=1
)

# 반환 예시:
# {
#   'success': True,
#   'reservation_number': 'R20251121001',
#   'selected_site': '00040009',
#   'target_date': '2025-11-21'
# }
```

---

## 사용 예제

### 기본 사용법

```python
from app.scrapers.xticket_scraper import XTicketScraper
import os

SHOP_ENCODE = os.getenv('XTICKET_SHOP_ENCODE')
SHOP_CODE = os.getenv('XTICKET_SHOP_CODE')
USER_ID = os.getenv('XTICKET_USER_ID')
PASSWORD = os.getenv('XTICKET_PASSWORD')

with XTicketScraper(SHOP_ENCODE, SHOP_CODE) as scraper:
    # 1. 로그인
    if scraper.login(USER_ID, PASSWORD):

        # 2. 예약 가능한 사이트 확인
        available_sites = scraper.get_available_sites(
            target_date="2025-11-21",
            product_group_code="0004"
        )

        print(f"예약 가능한 사이트: {len(available_sites)}개")
        for site in available_sites:
            print(f"  - {site['product_name']} ({site['product_code']})")

        # 3. 우선순위 목록 생성 (예: 처음 3개 사이트)
        priority_sites = [site['product_code'] for site in available_sites[:3]]

        # 4. 예약 실행
        result = scraper.make_reservation(
            target_date="2025-11-21",
            product_codes=priority_sites,
            product_group_code="0004",
            book_days=1
        )

        if result['success']:
            print(f"✅ 예약 성공!")
            print(f"   예약번호: {result['reservation_number']}")
            print(f"   선택된 사이트: {result['selected_site']}")
        else:
            print(f"❌ 예약 실패: {result['error']}")
```

### 자동화 시나리오

```python
from datetime import datetime, timedelta
from app.scrapers.xticket_scraper import XTicketScraper
import time

# 특정 날짜가 오픈되는 순간 예약하기
target_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
priority_sites = ['00040009', '00040010', '00040012', '00040013', '00040017']

with XTicketScraper(SHOP_ENCODE, SHOP_CODE) as scraper:
    scraper.login(USER_ID, PASSWORD)

    # 예약 오픈 시간까지 대기 (예: 오전 9시)
    while datetime.now().hour < 9:
        time.sleep(10)

    # 예약 오픈과 동시에 실행
    result = scraper.make_reservation(
        target_date=target_date,
        product_codes=priority_sites,
        product_group_code="0004",
        book_days=1
    )

    print(result)
```

---

## CAPTCHA 해결 시스템

### CAPTCHA Solver 구현

**파일**: `backend/app/utils/captcha_solver.py`

**주요 기능**:
1. **이미지 전처리**
   - 흑백 변환
   - 대비 향상 (2.0배)
   - 선명도 향상 (2.0배)
   - 노이즈 제거 (MedianFilter)
   - 이진화 (Threshold)

2. **OCR 엔진**
   - EasyOCR 사용 (GPU 비활성화)
   - 영어 인식 모드
   - 특수문자 제거

3. **재시도 로직**
   - 첫 시도: 전처리 적용
   - 재시도: 원본 이미지 사용

### 성능 최적화

- **싱글톤 패턴**: EasyOCR Reader를 재사용하여 초기화 시간 단축
- **조기 실패**: CAPTCHA 해결 실패 시 빠르게 다음 사이트로 이동
- **병렬 처리 가능**: 여러 세션에서 독립적으로 예약 시도 가능

---

## 의존성

### 추가된 패키지

```txt
# OCR (CAPTCHA 해결용)
easyocr==1.7.0
Pillow==10.1.0
```

### 설치 방법

```bash
cd backend
pip install -r requirements.txt
```

**참고**: EasyOCR 첫 실행 시 학습 모델을 다운로드하므로 시간이 걸릴 수 있습니다 (~100MB).

---

## 테스트 가이드

### 1. 개별 사이트 조회 테스트

```bash
cd backend
python -c "
from app.scrapers.xticket_scraper import XTicketScraper
import os
from dotenv import load_dotenv

load_dotenv()

with XTicketScraper(
    os.getenv('XTICKET_SHOP_ENCODE'),
    os.getenv('XTICKET_SHOP_CODE')
) as scraper:
    scraper.login(os.getenv('XTICKET_USER_ID'), os.getenv('XTICKET_PASSWORD'))

    sites = scraper.get_available_sites('2025-11-21', '0004')
    print(f'Available sites: {len(sites)}')
    for site in sites:
        print(f\"  - {site['product_name']}: {site['product_code']}\")
"
```

### 2. CAPTCHA 해결 테스트

```bash
cd backend
python test_captcha.py
```

---

## 에러 핸들링

### CAPTCHA 오류
- **증상**: `'자동입력' in error_msg`
- **처리**: 같은 사이트에서 새 CAPTCHA로 재시도

### 사이트 예약 완료
- **증상**: `select_yn == "0"`
- **처리**: 다음 우선순위 사이트로 이동

### 네트워크 오류
- **증상**: `requests.exceptions.RequestException`
- **처리**: 다음 사이트로 이동 후 계속 시도

### 로그인 필요
- **증상**: `is_logged_in == False`
- **처리**: 즉시 실패 반환, 재로그인 필요

---

## 성공률 향상 팁

### 1. 우선순위 목록 최적화
- **5-10개 사이트**: 너무 적으면 실패 확률 증가, 너무 많으면 시간 낭비
- **인접 사이트 선택**: 한 구역의 사이트들이 동시에 오픈되는 경향

### 2. CAPTCHA 인식률 향상
- **EasyOCR 모델 사전 다운로드**: 첫 실행 전 미리 초기화
- **필요시 2Captcha 서비스 사용**: 99%+ 정확도 ($1-3/1000회)

### 3. 타이밍 최적화
- **예약 오픈 시간 정확히 파악**: 보통 오전 9시 또는 10시
- **서버 시간과 동기화**: NTP 서버 사용 권장

### 4. 네트워크 최적화
- **유선 연결 사용**: WiFi보다 안정적
- **낮은 레이턴시**: 서버와 물리적으로 가까운 위치

---

## 다음 단계

### 우선순위 높음
1. **실전 테스트**: 실제 예약 오픈 시간에 테스트
2. **에러 로깅 강화**: 모든 실패 케이스 기록
3. **알림 시스템 통합**: 예약 성공/실패 시 텔레그램 알림

### 우선순위 중간
1. **예약 취소 API 구현**: 예약 취소 기능 추가
2. **예약 내역 조회 API**: 내 예약 목록 확인
3. **결제 API 연동**: 자동 결제 기능 (선택사항)

### 우선순위 낮음
1. **CAPTCHA 정확도 모니터링**: 인식 성공률 추적
2. **멀티 세션 지원**: 여러 계정으로 동시 예약
3. **GUI 개발**: 설정 및 모니터링 대시보드

---

## 참고 자료

- [XTICKET_API_ANALYSIS.md](./XTICKET_API_ANALYSIS.md) - API 상세 분석
- [XTICKET_IMPLEMENTATION_UPDATE.md](./XTICKET_IMPLEMENTATION_UPDATE.md) - 초기 구현 문서
- [captcha_solver.py](../backend/app/utils/captcha_solver.py) - CAPTCHA 해결 유틸리티
- [xticket_scraper.py](../backend/app/scrapers/xticket_scraper.py) - 메인 스크래퍼

---

**문서 끝**
