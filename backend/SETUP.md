# 🚀 빠른 설정 가이드

## 1. .env 파일 생성

```bash
cd backend
cp .env.example .env
```

그리고 `.env` 파일을 편집기로 열어서 실제 값을 입력하세요.

## 2. XTicket 자격증명 입력

`.env` 파일에서 다음 부분을 수정:

```bash
# XTicket 자격증명
XTICKET_USER_ID=실제_아이디
XTICKET_PASSWORD=실제_비밀번호
XTICKET_NAME=홍길동
XTICKET_PHONE=01012345678
XTICKET_CAR_NUMBER=12가3456
```

## 3. 텔레그램 봇 설정 (선택사항)

텔레그램 알림을 받으려면:

```bash
# 텔레그램
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 텔레그램 봇 만들기:

1. 텔레그램에서 [@BotFather](https://t.me/botfather) 검색
2. `/newbot` 명령어 입력
3. 봇 이름 설정
4. Bot Token 복사 → `TELEGRAM_BOT_TOKEN`에 입력

### Chat ID 얻기:

1. 봇에게 아무 메시지나 보내기
2. 브라우저에서 다음 URL 접속:
   ```
   https://api.telegram.org/bot[BOT_TOKEN]/getUpdates
   ```
3. `"chat":{"id":123456789}` 부분 찾기
4. ID 복사 → `TELEGRAM_CHAT_ID`에 입력

## 4. 완료!

이제 사용 가능합니다:

```bash
# 의존성 설치
pip install -r requirements.txt
pip install python-dotenv

# 테스트
python test_xticket.py

# Flask 앱 실행
python run.py
```

## ⚠️ 중요!

- `.env` 파일은 **절대 Git에 커밋하지 마세요**
- 이미 `.gitignore`에 추가되어 있어서 자동으로 무시됩니다
- 본인 컴퓨터에만 보관하세요
