# 드라이런 모드 (Dry Run Mode)

**작성일**: 2025-11-20

---

## 개요

실제 예약을 하지 않고 전체 프로세스를 테스트할 수 있는 **안전 모드**입니다.

---

## 사용법

### 1. 드라이런 모드 활성화

`backend/.env` 파일에서 설정:

```bash
XTICKET_DRY_RUN=true  # 드라이런 모드 활성화 (기본값)
```

### 2. 실제 예약 모드

```bash
XTICKET_DRY_RUN=false  # 실제 예약 실행
```

---

## 드라이런 모드 동작

### ✅ 실행되는 작업
1. 로그인
2. CAPTCHA 다운로드 및 해결
3. 예약 가능 사이트 조회
4. 예약 데이터 준비

### ❌ 실행되지 않는 작업
1. **실제 예약 API 호출**
2. **예약 문자 발송**
3. **결제 진행**

### 📋 출력 예시

```
4. 하이브리드 OCR로 CAPTCHA 해결 중...
   ✅ EasyOCR로 해결: '9669'

5. 예약 API 호출 (product_code: 00040009)
   요청 데이터: {'product_group_code': '0004', 'play_date': '20251121', 'product_code': '00040009', 'captcha': '9669'}

🧪 DRY RUN MODE - 실제 예약하지 않음

6. 예약 API 응답:
{
  "data": {
    "success": true,
    "book_no": "DRY_RUN_TEST",
    "message": "테스트 모드 - 실제 예약 안 함"
  }
}

✅✅✅ 예약 성공! ✅✅✅
   예약번호: DRY_RUN_TEST
```

---

## 실전 사용 시나리오

### 시나리오 1: 테스트
```bash
# .env
XTICKET_DRY_RUN=true

# 실행
python test_captcha_direct.py
```

**결과**:
- ✅ CAPTCHA 해결 확인
- ✅ 로직 검증
- ❌ 실제 예약 안 함

### 시나리오 2: 실제 예약
```bash
# .env
XTICKET_DRY_RUN=false

# 실행
python test_captcha_direct.py
```

**결과**:
- ✅ CAPTCHA 해결
- ✅ 실제 예약 API 호출
- ✅ 예약 번호 발급
- ✅ 예약 문자 수신

---

## 주의사항

### ⚠️  실제 예약 모드 사용 시

1. **결제 기한 확인**
   - 예약 후 10분 내 결제 필요
   - 미결제 시 자동 취소

2. **예약 취소**
   - 웹사이트: https://camp.xticket.kr → 마이페이지 → 예약내역
   - 예약 번호로 취소 가능

3. **테스트 금지 날짜**
   - 실제 원하는 날짜로만 테스트
   - 불필요한 예약으로 타인에게 피해 주지 않기

---

## 프로그래밍 방식 사용

```python
import os
from app.scrapers.xticket_scraper import XTicketScraper

# 드라이런 모드 활성화
os.environ['XTICKET_DRY_RUN'] = 'true'

with XTicketScraper(SHOP_ENCODE, SHOP_CODE) as scraper:
    scraper.login(USER_ID, PASSWORD)

    available = scraper.get_available_sites('2025-11-21', '0004')
    priority_sites = [s['product_code'] for s in available[:5]]

    # 드라이런 모드에서는 실제 예약 안 함
    result = scraper.make_reservation(
        target_date='2025-11-21',
        product_codes=priority_sites,
        product_group_code='0004'
    )

    print(f"예약 결과: {result}")
    # {'success': True, 'reservation_number': 'DRY_RUN_TEST', 'dry_run': True}
```

---

## FAQ

### Q1: 드라이런 모드에서 CAPTCHA를 해결하나요?
**A**: 네, CAPTCHA는 실제로 해결합니다. 단, 예약 API만 호출하지 않습니다.

### Q2: 드라이런 모드에서 세션이 유지되나요?
**A**: 네, 로그인 세션은 유지됩니다. 실제 예약만 하지 않습니다.

### Q3: 실수로 실제 예약이 되면?
**A**: `.env`에서 `XTICKET_DRY_RUN=true`로 설정되어 있으면 절대 실제 예약이 되지 않습니다.

### Q4: 실제 예약으로 바꾸려면?
**A**: `.env`에서 `XTICKET_DRY_RUN=false`로 변경 후 재실행

---

## 김해시민 감면 (TODO)

현재는 **기본 예약만** 지원합니다. 김해시민 감면을 받으려면:

1. 웹사이트에서 감면 선택 후 예약 진행
2. 개발자도구(F12) Network 탭에서 API 확인
3. 어떤 파라미터가 추가되는지 분석 필요

감면 API가 확인되면 추가 구현 예정입니다.

---

**문서 끝**
