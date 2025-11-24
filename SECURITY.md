# 보안 가이드

## 구현된 보안 기능

### 1. **비밀번호 해싱 (bcrypt)**
- 비밀번호를 평문이 아닌 bcrypt 해시로 저장
- Salt를 자동으로 생성하여 레인보우 테이블 공격 방지
- 하위 호환성 유지 (평문 비밀번호도 지원하지만 권장하지 않음)

**사용 방법:**
```bash
# 새 비밀번호 해시 생성
cd backend
venv\Scripts\python.exe -c "from app.utils.auth import generate_password_hash; print(generate_password_hash('your_password'))"

# .env 파일에 추가
ADMIN_PASSWORD_HASH=생성된_해시값
```

### 2. **Rate Limiting**
- 로그인 시도: **1분에 5번**까지 제한
- 전체 API: 일 200회, 시간당 50회 제한
- Brute Force 공격 방지
- IP 기반 제한 (Flask-Limiter)

**설정 변경:**
```python
# app/__init__.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
)

# 특정 엔드포인트
@limiter.limit("5 per minute")
```

### 3. **세션 보안**
- **HttpOnly**: JavaScript에서 쿠키 접근 차단 (XSS 방지)
- **SameSite=Lax**: CSRF 공격 완화
- **Secure Flag**: HTTPS 사용 시 자동 활성화 (프로덕션)
- **세션 만료**: 24시간 후 자동 만료

### 4. **API 인증**
- 모든 민감한 API 엔드포인트에 `@require_auth` 데코레이터 적용
- 인증되지 않은 요청은 401 Unauthorized 반환
- 세션 기반 인증 (쿠키)

**보호되는 엔드포인트:**
- 캠핑장 관리 (GET, POST, DELETE)
- 모니터링 (시작, 중지, 상태, 스케줄)
- 예약 관리 (조회, 생성, 상세)
- 통계 조회
- XTicket 연동

**인증 불필요:**
- `/api/health` (헬스 체크)
- `/api/auth/login` (로그인)
- `/api/auth/check` (인증 상태 확인)

### 5. **로깅 및 감사**
- 모든 로그인 시도 기록 (성공/실패, IP 주소)
- 실패한 로그인 시도에 대한 경고 로그
- 사용자 활동 추적 가능

**로그 예시:**
```
✅ User logged in: admin from IP: 192.168.1.100
⚠️  Failed login attempt for user: hacker from IP: 192.168.1.200
```

## 보안 모범 사례

### 1. 비밀번호 관리
```bash
# ✅ 권장: 해시 사용
ADMIN_PASSWORD_HASH=$2b$12$...

# ❌ 비권장: 평문 사용
ADMIN_PASSWORD=admin123
```

### 2. SECRET_KEY 변경
```bash
# 강력한 SECRET_KEY 생성
python -c "import secrets; print(secrets.token_hex(32))"

# .env에 설정
SECRET_KEY=생성된_키
```

### 3. HTTPS 사용 (프로덕션)
```python
# config.py - ProductionConfig
SESSION_COOKIE_SECURE = True  # HTTPS 전용
```

### 4. 환경 변수 보호
```bash
# ❌ 절대 .env 파일을 Git에 커밋하지 마세요
# ✅ .gitignore에 추가되어 있는지 확인
.env
```

### 5. 로그 모니터링
```bash
# 실패한 로그인 시도 확인
tail -f logs/app.log | grep "Failed login"
```

## 취약점 대응

### 1. Brute Force 공격
- **Rate Limiting**: 1분에 5번 시도 제한
- **로깅**: 모든 실패 시도 기록
- **대응**: 의심스러운 IP 주소 차단 가능

### 2. XSS (Cross-Site Scripting)
- **HttpOnly 쿠키**: JavaScript에서 세션 쿠키 접근 불가
- **Flask 자동 이스케이프**: 템플릿에서 XSS 방지

### 3. CSRF (Cross-Site Request Forgery)
- **SameSite=Lax**: 외부 사이트에서 쿠키 전송 제한
- **CORS 설정**: 허용된 origin만 API 접근 가능

### 4. Session Hijacking
- **HttpOnly + Secure**: 쿠키 도난 방지
- **세션 만료**: 24시간 후 자동 만료
- **로그아웃**: 명시적 세션 삭제

### 5. SQL Injection
- **ORM 사용**: SQLAlchemy로 자동 방어
- **파라미터화된 쿼리**: 직접 SQL 작성 시 주의

## 보안 체크리스트

### 개발 환경
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] 기본 비밀번호를 변경했는지 확인
- [ ] 로그에 민감한 정보가 기록되지 않는지 확인

### 프로덕션 배포 전
- [ ] `SECRET_KEY`를 강력한 값으로 변경
- [ ] `ADMIN_PASSWORD_HASH` 사용 (평문 제거)
- [ ] `SESSION_COOKIE_SECURE=True` 설정 (HTTPS 사용 시)
- [ ] CORS 설정에서 프로덕션 도메인만 허용
- [ ] Rate Limiting 제한값 조정 (필요 시)
- [ ] 텔레그램 토큰 등 API 키 확인

### 운영 중
- [ ] 정기적으로 로그 확인
- [ ] 의심스러운 로그인 시도 모니터링
- [ ] 의존성 업데이트 (보안 패치)
- [ ] 백업 주기적 실행

## Rate Limiting 우회 대응

공격자가 여러 IP를 사용하여 Rate Limiting을 우회하는 경우:

```python
# app/__init__.py - 추가 보안 레이어
# 사용자 이름 기반 제한 추가 가능
from flask import request

def get_user_from_request():
    data = request.get_json(silent=True)
    return data.get('username') if data else 'anonymous'

limiter = Limiter(
    key_func=lambda: f"{request.remote_addr}:{get_user_from_request()}"
)
```

## 긴급 대응

### 계정 잠금 (공격 감지 시)
```python
# .env 파일 수정
ADMIN_USERNAME=new_admin_name  # 사용자 이름 변경
ADMIN_PASSWORD_HASH=new_hash    # 비밀번호 재설정
```

### 모든 세션 무효화
```bash
# 서버 재시작으로 모든 활성 세션 삭제
# 또는 SECRET_KEY 변경
```

## 문의

보안 취약점을 발견하셨나요? Issues에 보고해주세요 (민감한 정보 제외).
