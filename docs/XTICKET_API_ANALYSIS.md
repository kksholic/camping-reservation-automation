# XTicket API 분석 문서

**생성일**: 2025-11-20
**분석 대상**: 생림오토캠핑장 (camp.xticket.kr)
**분석 방법**: Chrome DevTools 네트워크 분석

---

## 기본 정보

### Base URL
```
https://camp.xticket.kr
```

### 공통 헤더
```http
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
X-Requested-With: XMLHttpRequest
Accept: */*
Referer: https://camp.xticket.kr/web/main?shopEncode={shop_encode}
```

### 캠핑장 식별자
- **shop_encode**: `f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940` (URL 파라미터)
- **shop_code**: `622830018001` (API 요청용)

---

## 1. 로그인 API

### 엔드포인트
```
POST /Web/Member/MemberLogin.json
```

### 요청
```http
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

member_id=rltjd0627&member_password=Create89%40%40&shopCode=622830018001
```

**파라미터**:
- `member_id` (string, required): 사용자 아이디
- `member_password` (string, required): 사용자 비밀번호 (URL 인코딩)
- `shopCode` (string, required): 캠핑장 코드

### 응답
```json
{
  "data": {
    "success": true,
    "member_id": "rltjd0627",
    "member_no": 713632,
    "region_code": "4825013200",
    "blacklist_yn": "0",
    "blacklist_start_date": "0000-00-00",
    "blacklist_end_date": "0000-00-00",
    "password_change_yn": "0"
  }
}
```

**응답 필드**:
- `success` (boolean): 로그인 성공 여부
- `member_id` (string): 사용자 아이디
- `member_no` (integer): 회원 번호
- `region_code` (string): 지역 코드
- `blacklist_yn` (string): 블랙리스트 여부 ("0": 아님)
- `password_change_yn` (string): 비밀번호 변경 필요 여부

---

## 2. 예약 가능 날짜 조회 API

### 엔드포인트
```
POST /Web/Book/GetBookPlayDate.json
```

### 요청
```http
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

play_month=202511
```

**파라미터**:
- `play_month` (string, required): 조회할 월 (YYYYMM 형식)

### 응답
```json
{
  "data": {
    "bookPlayDateList": [
      {
        "play_date": "20251121",
        "book_remain_count": 49,
        "advance_yn": "0"
      },
      {
        "play_date": "20251122",
        "book_remain_count": 0,
        "advance_yn": "0"
      },
      {
        "play_date": "20251123",
        "book_remain_count": 105,
        "advance_yn": "0"
      }
    ]
  }
}
```

**응답 필드**:
- `bookPlayDateList` (array): 예약 가능 날짜 목록
  - `play_date` (string): 날짜 (YYYYMMDD 형식)
  - `book_remain_count` (integer): 예약 가능 잔여 수량 (0이면 예약 불가)
  - `advance_yn` (string): 사전 예약 여부

**활용**:
- `book_remain_count > 0`: 예약 가능
- `book_remain_count = 0`: 예약 불가 (매진)

---

## 3. 시설(상품) 그룹 조회 API

### 엔드포인트
```
POST /Web/Book/GetBookProductGroup.json
```

### 요청
```http
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

start_date=20251101&end_date=20251131
```

**파라미터**:
- `start_date` (string, required): 시작 날짜 (YYYYMMDD 형식)
- `end_date` (string, required): 종료 날짜 (YYYYMMDD 형식)

### 응답
```json
{
  "data": {
    "bookProductGroupList": [
      {
        "product_group_code": "0001",
        "product_group_name": "잔디사이트",
        "product_group_kind": "010001",
        "product_fee": 30000,
        "stay_discount_yn": "0",
        "stay_discount_value": 0,
        "product_map_file_path": "/productmap",
        "product_map_file_name": "/622830018001/20231115155939751_map_0001.jpg"
      },
      {
        "product_group_code": "0002",
        "product_group_name": "데크사이트",
        "product_fee": 30000
      },
      {
        "product_group_code": "0004",
        "product_group_name": "파쇄석사이트",
        "product_fee": 30000
      }
    ]
  }
}
```

**응답 필드**:
- `bookProductGroupList` (array): 시설 그룹 목록
  - `product_group_code` (string): 시설 그룹 코드
  - `product_group_name` (string): 시설 그룹 이름
  - `product_fee` (integer): 이용 요금 (원)
  - `stay_discount_yn` (string): 숙박 할인 여부
  - `product_map_file_name` (string): 시설 배치도 파일 경로

**시설 종류**:
1. 잔디사이트 (코드: 0001)
2. 데크사이트 (코드: 0002)
3. 파쇄석사이트 (코드: 0004)

---

## 4. 캠핑장 정보 조회 API

### 엔드포인트
```
POST /Web/Book/GetShopInformation.json
```

### 요청
```http
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

shop_encode=f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940
```

**파라미터**:
- `shop_encode` (string, required): 캠핑장 고유 인코딩 값

### 응답
```json
{
  "data": {
    "shop_code": "622830018001",
    "shop_name": "생림오토캠핑장",
    "shop_encode": "f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940",
    "company_code": "6228300180",
    "book_kind": "070001",
    "book_days": 2,
    "book_day_limit_count": 1,
    "book_month_limit_count": 31,
    "max_book_count": 0,
    "play_month": "202511",
    "reservation_yn": "0",
    "join_limit_age": 19,
    "web_payment_kind": "CARD,VBANK",
    "web_store_id": "xticket02m",
    "mobile_store_id": "xticket03m",
    "web_store_key": "4kelF1/vzRK3Uk6OD2WHuBYABhPVoUGWArhQ8ptxDMKy3ahAGla4hpM2CNvMFgU9b5M9dSMxNenSn3bh0BGq7Q==",
    "web_cancel_key": "chusa6503u",
    "sms_reply_phone_no": "0553389925",
    "pre_enter_minite": 30,
    "member_identification_kind": "MOBILE,IPIN",
    "advance_ddays": 0,
    "advance_period": "",
    "advance_target": "",
    "advance_name": "",
    "advance_proof": "",
    "advnace_play_month": "",
    "two_stay_days": 0,
    "warning_text": "",
    "drone_url": ""
  }
}
```

**주요 응답 필드**:
- `shop_code` (string): 캠핑장 코드 (로그인 시 사용)
- `shop_name` (string): 캠핑장 이름
- `book_days` (integer): 기본 숙박일 (2일 = 1박2일)
- `book_day_limit_count` (integer): 1일 예약 가능 사이트 수 (1개)
- `book_month_limit_count` (integer): 1개월 예약 가능 일수 (31일)
- `web_payment_kind` (string): 결제 방법 ("CARD,VBANK")
- `web_store_id` (string): PG 상점 ID
- `join_limit_age` (integer): 가입 최소 연령 (19세)

**활용**:
- `shop_code`: 로그인 API에서 `shopCode` 파라미터로 사용
- `book_day_limit_count`: 하루에 1사이트만 예약 가능
- `web_payment_kind`: 신용카드(CARD), 가상계좌(VBANK) 지원

---

## API 사용 예제

### Python (requests 라이브러리)

```python
import requests
from urllib.parse import urlencode

# 기본 설정
BASE_URL = "https://camp.xticket.kr"
SHOP_ENCODE = "f5f32b56abe23f9aec682e337c7ee65772a4438ff09b56823d4c7d2a7528d940"
SHOP_CODE = "622830018001"

# 공통 헤더
headers = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE_URL}/web/main?shopEncode={SHOP_ENCODE}'
}

session = requests.Session()
session.headers.update(headers)

# 1. 로그인
login_data = {
    'member_id': 'your_id',
    'member_password': 'your_password',
    'shopCode': SHOP_CODE
}
response = session.post(
    f'{BASE_URL}/Web/Member/MemberLogin.json',
    data=urlencode(login_data)
)
print("로그인:", response.json())

# 2. 예약 가능 날짜 조회
date_data = {'play_month': '202511'}
response = session.post(
    f'{BASE_URL}/Web/Book/GetBookPlayDate.json',
    data=urlencode(date_data)
)
print("예약 가능 날짜:", response.json())

# 3. 시설 그룹 조회
product_data = {
    'start_date': '20251101',
    'end_date': '20251131'
}
response = session.post(
    f'{BASE_URL}/Web/Book/GetBookProductGroup.json',
    data=urlencode(product_data)
}
print("시설 목록:", response.json())

# 4. 캠핑장 정보 조회
shop_data = {'shop_encode': SHOP_ENCODE}
response = session.post(
    f'{BASE_URL}/Web/Book/GetShopInformation.json',
    data=urlencode(shop_data)
)
print("캠핑장 정보:", response.json())
```

---

## 중요 발견 사항

### 1. shopEncode vs shopCode
- **shopEncode**: URL 파라미터용 (SHA-256 해시값)
- **shopCode**: API 요청용 (숫자 코드)
- 두 값은 다르며, 각각의 용도에 맞게 사용해야 함

### 2. Content-Type
- **올바른 형식**: `application/x-www-form-urlencoded; charset=UTF-8`
- **잘못된 형식**: `application/json` (작동하지 않음!)

### 3. 응답 구조
- 모든 API 응답은 `{data: {...}}` 래퍼 형식
- 성공 여부는 `data.success` 필드로 확인 (로그인 API)

### 4. 날짜 형식
- 요청: `YYYYMMDD` (예: "20251121")
- 응답: `YYYYMMDD` (예: "20251121")

### 5. Referer 검증
- XTicket은 Referer 헤더를 검증함
- 직접 접근 시 "세션 만료" 메시지 표시
- API 요청 시 반드시 올바른 Referer 포함 필요

### 6. 예약 제한
- 1일 1사이트만 예약 가능 (`book_day_limit_count: 1`)
- 최대 2박3일까지 예약 가능
- 매월 1일 오전 10시에 다음 달 예약 오픈

---

## 추가 조사 필요 항목

### 1. 예약 실행 API
- 엔드포인트: 아직 미확인 (예상: `/Web/Book/MakeReservation.json`)
- 실제 예약 버튼 클릭 시 분석 필요

### 2. 취소 API
- 예약 취소 관련 API 엔드포인트 확인 필요

### 3. 예약 내역 조회 API
- "예약내역(결제/취소)" 페이지 분석 필요
- URL: `/web/books?shopEncode=...`

### 4. 결제 API
- PG 연동 방식 확인 필요
- `web_store_id`, `web_store_key` 활용 방법

---

## 자동화 시 주의사항

### 법적/윤리적 고려사항
1. **이용약관 준수**: 사이트 양도 금지 규정 준수
2. **과도한 트래픽 방지**: 적절한 요청 간격 유지 (최소 30초)
3. **개인 용도**: 상업적 목적이나 대량 예약 금지
4. **신분증 지참**: 예약자 본인 확인 절차 준수

### 기술적 고려사항
1. **세션 관리**: 쿠키 기반 세션 유지 필요
2. **에러 핸들링**: 네트워크 오류, API 응답 오류 처리
3. **재시도 로직**: 실패 시 최대 3회 재시도
4. **로깅**: 모든 요청/응답 기록 (디버깅용)

---

## 버전 이력

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| 1.0 | 2025-11-20 | 초기 문서 작성 (로그인, 날짜 조회, 시설 조회, 캠핑장 정보 API) |

---

**문서 끝**
