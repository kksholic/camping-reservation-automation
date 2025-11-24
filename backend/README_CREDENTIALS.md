# 자격증명 관리 가이드

## 🔐 보안 방법 비교

| 방법 | 보안 수준 | 난이도 | 사용 상황 |
|------|----------|--------|----------|
| 평문 파일 | ❌ 매우 낮음 | 쉬움 | **절대 사용 금지!** |
| .env 파일 | ⚠️ 낮음 | 쉬움 | 개발 환경 |
| 암호화 파일 | ✅ 높음 | 보통 | **권장** |
| 시스템 키체인 | ✅ 매우 높음 | 어려움 | 프로덕션 |

## 💡 권장 방법: 암호화 파일

### 1. 자격증명 저장 (최초 1회)

```bash
cd backend
python credentials_manager.py save
```

**입력 내용:**
```
사용자 ID: your_xticket_id
비밀번호: your_password
이름: 홍길동
휴대폰: 01012345678
차량번호: 12가3456

마스터 비밀번호: [암기하기 쉬운 강력한 비밀번호]
```

**생성되는 파일:**
- `credentials.enc` - 암호화된 자격증명 (AES-256)
- `.credentials.salt` - 암호화 솔트

⚠️ **마스터 비밀번호는 절대 잊지 마세요!** 복구 불가능합니다.

### 2. 자격증명 조회

```bash
python credentials_manager.py get
```

마스터 비밀번호를 입력하면 자격증명이 표시됩니다.

### 3. 코드에서 사용

```python
from credentials_manager import CredentialsManager
import getpass

# 마스터 비밀번호 입력
master_password = getpass.getpass("마스터 비밀번호: ")

# 자격증명 로드
manager = CredentialsManager()
creds = manager.load_credentials(master_password)

# 사용
user_id = creds['user_id']
password = creds['password']
```

## 🔒 보안 원리

### 암호화 방식
- **알고리즘**: AES-256 (Fernet)
- **키 유도**: PBKDF2 + SHA-256
- **반복 횟수**: 100,000회
- **Salt**: 랜덤 16바이트

### 보안 강도
```
마스터 비밀번호 (8자+)
  → PBKDF2 (100,000회 반복)
    → AES-256 암호화 키
      → 자격증명 암호화
```

**공격자가 파일을 얻어도:**
- ❌ 마스터 비밀번호 없이는 복호화 불가능
- ❌ 무차별 대입 공격 매우 어려움 (100,000회 반복)

## 📋 파일 관리

### .gitignore 설정 (필수!)
```
# 자격증명 파일 (절대 커밋 금지!)
credentials.enc
.credentials.salt
.env
```

### 백업
```bash
# 안전한 외부 저장소에 백업
cp credentials.enc /path/to/secure/backup/
cp .credentials.salt /path/to/secure/backup/
```

## 🚨 주의사항

### ❌ 절대 하지 말 것
- Git에 `credentials.enc` 커밋
- 마스터 비밀번호를 코드에 하드코딩
- 평문 비밀번호 파일 사용
- 마스터 비밀번호를 .env에 저장

### ✅ 해야 할 것
- 강력한 마스터 비밀번호 사용 (12자 이상)
- 마스터 비밀번호 안전하게 기억
- .gitignore에 자격증명 파일 추가
- 정기적으로 비밀번호 변경

## 🔄 대안: .env 파일 (간단)

암호화가 과하다면 .env 파일 사용:

```bash
# backend/.env
XTICKET_USER_ID=your_id
XTICKET_PASSWORD=your_password
XTICKET_NAME=홍길동
XTICKET_PHONE=01012345678
XTICKET_CAR_NUMBER=12가3456
```

**코드에서 사용:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

user_id = os.getenv('XTICKET_USER_ID')
password = os.getenv('XTICKET_PASSWORD')
```

**장점:**
- ✅ 간단함
- ✅ .gitignore로 보호

**단점:**
- ⚠️ 파일 자체는 평문
- ⚠️ PC 접근 권한 있으면 읽을 수 있음

## 💼 프로덕션 환경

### Docker Secrets 사용
```yaml
# docker-compose.yml
secrets:
  xticket_credentials:
    file: ./credentials.enc
```

### 환경 변수로 주입
```bash
docker run -e XTICKET_USER_ID=xxx -e XTICKET_PASSWORD=xxx ...
```

## 📞 문제 해결

### "잘못된 마스터 비밀번호" 에러
- 마스터 비밀번호를 정확히 입력했는지 확인
- 대소문자, 공백 주의

### 마스터 비밀번호를 잊어버렸을 때
- 😢 **복구 불가능합니다**
- 새로 저장: `python credentials_manager.py save`

### Git에 실수로 커밋한 경우
```bash
# 히스토리에서 완전 삭제
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch credentials.enc" \
  --prune-empty --tag-name-filter cat -- --all

# 강제 푸시
git push origin --force --all
```

## 🎓 권장 사항

**개인 프로젝트:**
- ✅ 암호화 파일 (`credentials_manager.py`)
- ✅ .gitignore 설정

**팀 프로젝트:**
- ✅ 각자 개인 암호화 파일 사용
- ✅ 마스터 비밀번호는 공유하지 않음

**프로덕션:**
- ✅ 시스템 키체인 또는 클라우드 비밀 관리자
- ✅ AWS Secrets Manager, Azure Key Vault 등
