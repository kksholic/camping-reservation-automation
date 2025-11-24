# CLAUDE.md

캠핑 예약 자동화 시스템 - Claude Code 가이드

## 프로젝트 개요

**목적**: 여러 캠핑 예약 사이트를 통합 관리하고 예약 프로세스를 자동화하는 웹 애플리케이션

**핵심 특징**:
- Flask 백엔드 + React 프론트엔드 풀스택 웹 애플리케이션
- Docker 컨테이너 기반 배포
- 실시간 모니터링 및 자동 예약
- 텔레그램 알림 시스템

## 기술 스택

### 백엔드
- **Python 3.11+** - 프로그래밍 언어
- **Flask 3.0** - 웹 프레임워크
- **Flask-CORS** - CORS 처리
- **Flask-SQLAlchemy** - ORM
- **Playwright** - 브라우저 자동화
- **APScheduler** - 백그라운드 작업 스케줄링
- **python-telegram-bot** - 텔레그램 알림
- **SQLite** - 데이터베이스
- **Loguru** - 로깅

### 프론트엔드
- **React 18** - UI 라이브러리
- **Vite** - 빌드 도구 (Create React App 대체)
- **Material-UI (MUI)** - UI 컴포넌트 라이브러리
- **React Router v6** - 클라이언트 사이드 라우팅
- **Axios** - HTTP 클라이언트

### 인프라
- **Docker** - 컨테이너화
- **Nginx** - 프론트엔드 웹 서버 및 API 프록시
- **Docker Compose** - 멀티 컨테이너 오케스트레이션

## 아키텍처

### 전체 구조
```
User → Nginx (Port 80) → React Frontend
                       ↓ /api
                       → Flask Backend (Port 5000)
                       ↓
                       → Playwright → 캠핑 사이트
                       ↓
                       → Telegram Bot API
```

### 디렉토리 구조
```
camping-reservation-automation/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask 앱 팩토리
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py        # API 엔드포인트
│   │   ├── scrapers/
│   │   │   ├── base_scraper.py  # 추상 베이스 클래스
│   │   │   ├── gocamp_scraper.py
│   │   │   └── naver_scraper.py
│   │   ├── services/
│   │   │   ├── monitor_service.py      # 모니터링 로직
│   │   │   └── reservation_service.py  # 예약 로직
│   │   ├── notifications/
│   │   │   └── telegram_notifier.py
│   │   └── models/
│   │       └── database.py      # SQLAlchemy 모델
│   ├── config.py                # 환경별 설정
│   ├── run.py                   # 진입점
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Navigation.jsx   # 사이드바 네비게이션
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx    # 대시보드 페이지
│   │   │   ├── CampingSites.jsx # 캠핑장 관리
│   │   │   ├── Monitoring.jsx   # 모니터링 관리
│   │   │   └── Reservations.jsx # 예약 내역
│   │   ├── services/
│   │   │   └── api.js           # API 클라이언트
│   │   ├── styles/
│   │   │   └── App.css
│   │   ├── App.jsx              # 메인 앱 컴포넌트
│   │   └── main.jsx             # 엔트리 포인트
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docker-compose.yml
├── data/                        # SQLite DB (gitignore)
└── logs/                        # 로그 파일 (gitignore)
```

## 데이터 흐름

### 1. 모니터링 프로세스
```
1. 사용자가 프론트엔드에서 모니터링 타겟 추가
2. POST /api/monitoring/targets → DB에 저장
3. 사용자가 "모니터링 시작" 클릭
4. POST /api/monitoring/start → APScheduler 시작
5. MonitorService가 60초마다 check_all_targets() 실행
6. BaseScraper 구현체로 각 사이트 확인
7. 상태 변경 감지 시 TelegramNotifier로 알림
8. DB 업데이트 및 프론트엔드에 상태 반영
```

### 2. 자동 예약 프로세스
```
1. 모니터링에서 예약 가능 상태 감지
2. ReservationService.create_reservation() 호출
3. Scraper가 예약 프로세스 자동 실행
4. 성공/실패 결과를 DB 저장
5. 텔레그램 알림 전송
6. 프론트엔드에 예약 내역 표시
```

## API 엔드포인트

### 헬스 체크
- `GET /api/health` - 서버 상태 확인

### 캠핑장 관리
- `GET /api/camping-sites` - 캠핑장 목록
- `POST /api/camping-sites` - 캠핑장 추가
- `DELETE /api/camping-sites/<id>` - 캠핑장 삭제

### 모니터링
- `GET /api/monitoring/targets` - 모니터링 타겟 목록
- `POST /api/monitoring/targets` - 타겟 추가
- `POST /api/monitoring/start` - 모니터링 시작
- `POST /api/monitoring/stop` - 모니터링 중지
- `GET /api/monitoring/status` - 모니터링 상태

### 예약
- `GET /api/reservations` - 예약 목록
- `GET /api/reservations/<id>` - 예약 상세
- `POST /api/reservations` - 수동 예약 생성

### 통계
- `GET /api/statistics` - 전체 통계

## 데이터베이스 스키마

### camping_sites
```sql
id: INTEGER PRIMARY KEY
name: TEXT NOT NULL
site_type: TEXT NOT NULL  -- 'gocamp', 'naver', 'custom'
url: TEXT NOT NULL
created_at: TIMESTAMP
```

### reservations
```sql
id: INTEGER PRIMARY KEY
camping_site_id: INTEGER FK
check_in_date: DATE NOT NULL
check_out_date: DATE NOT NULL
status: TEXT  -- 'monitoring', 'available', 'reserved', 'failed'
reservation_number: TEXT
error_message: TEXT
created_at: TIMESTAMP
updated_at: TIMESTAMP
```

### monitoring_targets
```sql
id: INTEGER PRIMARY KEY
camping_site_id: INTEGER FK
target_date: DATE NOT NULL
is_active: BOOLEAN
notification_sent: BOOLEAN
last_checked: TIMESTAMP
last_status: TEXT  -- 'available', 'unavailable'
created_at: TIMESTAMP
```

### user_info
```sql
id: INTEGER PRIMARY KEY
name: TEXT NOT NULL
phone: TEXT NOT NULL
car_number: TEXT
email: TEXT
created_at: TIMESTAMP
updated_at: TIMESTAMP
```

## 개발 가이드라인

### 코딩 규칙

#### Python (백엔드)
- **PEP 8** 준수
- `snake_case` 네이밍
- 타입 힌팅 사용 권장
- Docstring 작성 (Google 스타일)
- 120자 라인 제한

#### JavaScript/React (프론트엔드)
- **ESLint** 설정 준수
- `camelCase` 네이밍 (컴포넌트는 PascalCase)
- 함수형 컴포넌트 + Hooks 사용
- PropTypes 또는 TypeScript 권장

### 스크래퍼 개발

#### 새 스크래퍼 추가 방법
1. `backend/app/scrapers/` 에 `{site_name}_scraper.py` 생성
2. `BaseScraper` 상속
3. 필수 메서드 구현:
   - `check_availability(url, target_date)` → bool
   - `make_reservation(url, check_in, check_out, user_info)` → dict
   - `get_cancellation_info(url, target_date)` → list

4. `backend/app/services/monitor_service.py` 의 `scrapers` 딕셔너리에 추가

#### 예시
```python
from app.scrapers.base_scraper import BaseScraper

class CustomSiteScraper(BaseScraper):
    def check_availability(self, url: str, target_date: str) -> bool:
        self.init_browser(headless=True)
        try:
            self.page.goto(url)
            # 스크래핑 로직
            return True  # 또는 False
        finally:
            self.close_browser()

    # 나머지 메서드 구현...
```

### 프론트엔드 페이지 추가

1. `frontend/src/pages/` 에 새 페이지 컴포넌트 생성
2. `App.jsx` 에 Route 추가
3. `Navigation.jsx` 에 메뉴 항목 추가
4. 필요한 API 함수를 `services/api.js` 에 추가

## Docker 배포

### 개발 환경
```bash
docker-compose up
```

### 프로덕션 빌드
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 환경 변수 설정
`backend/.env` 파일 생성:
```bash
FLASK_ENV=production
SECRET_KEY=<강력한-시크릿-키>
TELEGRAM_BOT_TOKEN=<봇-토큰>
TELEGRAM_CHAT_ID=<채팅-ID>
BROWSER_HEADLESS=true
```

## 주의사항

### 보안
- **절대** `.env` 파일을 커밋하지 말 것
- SECRET_KEY는 프로덕션에서 반드시 변경
- 텔레그램 토큰 노출 주의

### 성능
- Playwright 브라우저 인스턴스 관리 (메모리 누수 방지)
- 스크래핑 간격 최소 30초 이상 유지
- 동시 다발적 요청 제한

### 법적/윤리
- 사이트 이용약관 준수
- robots.txt 확인
- 과도한 트래픽 방지
- 개인 용도로만 사용

## 트러블슈팅

### Playwright 설치 오류
```bash
# 시스템 의존성 설치
playwright install-deps
playwright install chromium
```

### CORS 오류
- `backend/config.py` 에서 `CORS_ORIGINS` 확인
- 프론트엔드 URL이 올바르게 설정되었는지 확인

### Docker 빌드 실패
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache
```

## 다음 단계

### 우선순위 높음
1. 고캠핑 스크래퍼 실제 구현
2. 네이버 예약 스크래퍼 실제 구현
3. 에러 핸들링 강화
4. 캠핑장 추가 다이얼로그 구현
5. 모니터링 시작/중지 버튼 연동

### 우선순위 중간
1. 사용자 정보 관리 페이지
2. 예약 상세 페이지
3. 로그 뷰어
4. 알림 설정 관리

### 우선순위 낮음
1. 통계 차트
2. 가격 추적 기능
3. 다크 모드
4. 모바일 반응형 개선

## 참고 자료

- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [React 공식 문서](https://react.dev/)
- [Playwright 문서](https://playwright.dev/python/)
- [Material-UI 문서](https://mui.com/)
- [python-telegram-bot 문서](https://docs.python-telegram-bot.org/)
