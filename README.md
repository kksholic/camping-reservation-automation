# 🏕️ 캠핑 예약 자동화 시스템

여러 캠핑 예약 사이트를 통합 관리하고 자동화하는 웹 애플리케이션입니다.

## ✨ 주요 기능

### 1. 실시간 예약 모니터링
- 여러 캠핑 예약 사이트 동시 모니터링
- 예약 가능 여부 실시간 확인
- 원하는 날짜/캠핑장 설정 및 추적

### 2. 자동 예약 실행
- 선착순 예약 자동 진행
- 사용자 정보 자동 입력
- 결제 전 단계까지 자동화

### 3. 취소 알림
- 예약 취소 발생 시 즉시 알림
- 대기 중인 날짜의 예약 가능 전환 감지

### 4. 텔레그램 알림
- 예약 성공/실패 알림
- 예약 가능 상태 변경 알림
- 시스템 상태 및 오류 알림

### 5. 웹 대시보드
- 직관적인 React 기반 UI
- 실시간 모니터링 현황
- 통계 및 예약 관리

## 🎯 지원 사이트

- **고캠핑** (gocamp.or.kr) - 한국관광공사 운영 공공 캠핑장
- **네이버 예약** - 네이버를 통한 캠핑장 예약
- **개별 캠핑장 사이트** - 확장 가능한 구조로 추가 가능

## 🛠️ 기술 스택

### 백엔드
- **Python 3.11+**
- **Flask** - 웹 프레임워크
- **Playwright** - 브라우저 자동화
- **SQLAlchemy** - ORM
- **SQLite** - 데이터베이스
- **APScheduler** - 작업 스케줄링
- **python-telegram-bot** - 텔레그램 알림

### 프론트엔드
- **React 18** - UI 라이브러리
- **Vite** - 빌드 도구
- **Material-UI** - UI 컴포넌트
- **Axios** - HTTP 클라이언트
- **React Router** - 라우팅

### 인프라
- **Docker** - 컨테이너화
- **Nginx** - 웹 서버 및 리버스 프록시
- **Docker Compose** - 오케스트레이션

## 📁 프로젝트 구조

```
camping-reservation-automation/
├── backend/                  # Flask 백엔드
│   ├── app/
│   │   ├── api/             # API 라우트
│   │   ├── scrapers/        # 사이트별 스크래퍼
│   │   ├── automation/      # 자동화 로직 (미사용)
│   │   ├── notifications/   # 텔레그램 알림
│   │   ├── models/          # DB 모델
│   │   └── services/        # 비즈니스 로직
│   ├── config.py            # 설정
│   └── run.py               # 진입점
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/      # UI 컴포넌트
│   │   ├── pages/           # 페이지
│   │   ├── services/        # API 서비스
│   │   └── styles/          # 스타일
│   └── package.json
├── docker/                   # Docker 설정
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docker-compose.yml        # Docker Compose 설정
├── data/                     # SQLite DB
└── logs/                     # 로그 파일
```

## 🚀 빠른 시작

### 사전 요구사항
- Docker 및 Docker Compose 설치
- 텔레그램 봇 토큰 및 Chat ID (선택사항)

### 1. 저장소 클론
```bash
git clone <repository-url>
cd camping-reservation-automation
```

### 2. 환경 변수 설정
```bash
# 백엔드 환경 변수
cp backend/.env.example backend/.env
# backend/.env 파일을 편집하여 설정값 입력

# 프론트엔드 환경 변수
cp frontend/.env.example frontend/.env
```

### 3. Docker로 실행
```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 4. 접속
- **프론트엔드**: http://localhost
- **백엔드 API**: http://localhost:5000/api

## 💻 로컬 개발 환경

### 빠른 시작 (Windows)
프로젝트 루트에서 `start-servers.bat` 파일을 실행하면 프론트엔드와 백엔드 서버가 자동으로 시작됩니다.

```bash
# 더블클릭하거나 명령줄에서 실행
start-servers.bat
```

**서버 주소**:
- **프론트엔드**: http://localhost:4000
- **백엔드 API**: http://localhost:5001/api

### 수동으로 서버 시작하기

#### 백엔드 개발
```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium

# 개발 서버 실행 (포트 5001)
python run.py
```

#### 프론트엔드 개발
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행 (포트 4000)
npm run dev
```

### 포트 변경 방법
기본 포트(프론트엔드: 4000, 백엔드: 5001)를 변경하려면:

1. **백엔드 포트 변경**:
   - `backend/.env` 파일에서 `FLASK_PORT` 수정
   - `CORS_ORIGINS`에 새 프론트엔드 포트 반영

2. **프론트엔드 포트 변경**:
   - `frontend/vite.config.js` 파일에서 `server.port` 수정
   - `frontend/src/services/api.js` 파일에서 `API_URL` 수정

## 📝 사용 방법

### 1. 캠핑장 등록
1. 웹 대시보드 접속
2. "캠핑장 관리" 메뉴
3. "캠핑장 추가" 버튼 클릭
4. 캠핑장 정보 입력

### 2. 모니터링 설정
1. "모니터링 관리" 메뉴
2. "타겟 추가" 버튼 클릭
3. 캠핑장 및 날짜 선택

### 3. 모니터링 시작
1. 대시보드에서 "모니터링 시작" 버튼 클릭
2. 텔레그램으로 알림 수신

### 4. 예약 확인
1. "예약 내역" 메뉴에서 상태 확인
2. 예약 성공 시 예약번호 표시

## ⚙️ 설정 옵션

### backend/.env
```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# 텔레그램
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# 모니터링
MONITORING_INTERVAL=60  # 60초마다 확인

# 브라우저
BROWSER_HEADLESS=true  # headless 모드
```

## 🔧 개발 로드맵

### Phase 1: 기본 인프라 ✅
- [x] 프로젝트 구조
- [x] Flask 백엔드 API
- [x] React 프론트엔드
- [x] Docker 설정

### Phase 2: 스크래핑 (진행 중)
- [ ] 고캠핑 스크래퍼 구현
- [ ] 네이버 예약 스크래퍼 구현
- [ ] 에러 핸들링 및 재시도 로직

### Phase 3: 자동화
- [ ] 모니터링 엔진 완성
- [ ] 자동 예약 봇
- [ ] 스케줄러 최적화

### Phase 4: 고급 기능
- [ ] 여러 캠핑장 동시 모니터링
- [ ] 예약 우선순위 설정
- [ ] 통계 및 리포트
- [ ] 가격 추적 기능

## ⚠️ 주의사항

### 법적/윤리적 고려사항
- 사이트 이용약관 준수
- 과도한 요청으로 서버 부하 방지 (기본 60초 간격)
- 개인정보 로컬 암호화 저장
- 상업적 용도 금지

### 보안
- `.env` 파일은 절대 커밋하지 않음
- 텔레그램 토큰 안전하게 관리
- 로그에 민감 정보 제외

## 🐛 트러블슈팅

### 포트 충돌 오류
다른 프로그램이 이미 포트를 사용 중인 경우:

**Windows에서 포트 사용 중인 프로세스 찾기**:
```bash
# 4000번 포트 사용 중인 프로세스 확인
netstat -ano | findstr :4000

# 5001번 포트 사용 중인 프로세스 확인
netstat -ano | findstr :5001

# 프로세스 종료 (PID는 위 명령어 결과에서 확인)
taskkill /F /PID <PID>
```

**포트 변경**:
- 위의 "포트 변경 방법" 섹션 참고

### Docker 빌드 실패
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache

# 볼륨 초기화
docker-compose down -v
```

### 브라우저 자동화 오류
```bash
# Playwright 재설치
playwright install chromium
playwright install-deps
```

### 데이터베이스 오류
```bash
# 데이터베이스 초기화
rm data/camping.db
# 애플리케이션 재시작하면 자동 생성
```

### CORS 오류
프론트엔드에서 API 호출 시 CORS 오류가 발생하는 경우:
1. `backend/.env` 파일의 `CORS_ORIGINS`에 프론트엔드 URL이 포함되어 있는지 확인
2. 포트 번호가 정확한지 확인 (기본값: http://localhost:4000)

## 📄 라이선스

MIT License

## 🤝 기여

이슈 및 PR은 언제든지 환영합니다!

## 📞 문의

프로젝트 관련 문의사항은 Issues를 통해 남겨주세요.
