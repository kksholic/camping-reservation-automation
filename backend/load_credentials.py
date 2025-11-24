"""
.env 파일에서 자격증명 로드하는 유틸리티

사용 예:
    from load_credentials import get_xticket_credentials

    creds = get_xticket_credentials()
    print(creds['user_id'])
    print(creds['password'])
"""
import os
from dotenv import load_dotenv


def get_xticket_credentials() -> dict:
    """
    .env 파일에서 XTicket 자격증명 로드

    Returns:
        {
            'user_id': str,
            'password': str,
            'name': str,
            'phone': str,
            'car_number': str
        }
    """
    # .env 파일 로드
    load_dotenv()

    credentials = {
        'user_id': os.getenv('XTICKET_USER_ID'),
        'password': os.getenv('XTICKET_PASSWORD'),
        'name': os.getenv('XTICKET_NAME', ''),
        'phone': os.getenv('XTICKET_PHONE', ''),
        'car_number': os.getenv('XTICKET_CAR_NUMBER', '')
    }

    # 필수 값 확인
    if not credentials['user_id']:
        raise ValueError("XTICKET_USER_ID가 .env 파일에 설정되지 않았습니다")

    if not credentials['password']:
        raise ValueError("XTICKET_PASSWORD가 .env 파일에 설정되지 않았습니다")

    return credentials


def get_telegram_config() -> dict:
    """
    .env 파일에서 텔레그램 설정 로드

    Returns:
        {
            'bot_token': str,
            'chat_id': str
        }
    """
    load_dotenv()

    return {
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID')
    }


if __name__ == "__main__":
    """테스트"""
    print("=" * 60)
    print("🔐 .env 파일 자격증명 로드 테스트")
    print("=" * 60)

    try:
        creds = get_xticket_credentials()

        print("\n✅ XTicket 자격증명 로드 성공!")
        print(f"\n사용자 ID: {creds['user_id']}")
        print(f"비밀번호: {'*' * len(creds['password'])}")
        print(f"이름: {creds['name']}")
        print(f"휴대폰: {creds['phone']}")
        print(f"차량번호: {creds['car_number']}")

    except ValueError as e:
        print(f"\n❌ 에러: {e}")
        print("\n📝 .env 파일을 생성하고 다음 값을 설정하세요:")
        print("   XTICKET_USER_ID=your_id")
        print("   XTICKET_PASSWORD=your_password")

    except Exception as e:
        print(f"\n❌ 예상치 못한 에러: {e}")

    print("\n" + "=" * 60)

    # 텔레그램 설정
    telegram = get_telegram_config()
    if telegram['bot_token'] and telegram['chat_id']:
        print("\n✅ 텔레그램 설정 로드 성공!")
        print(f"Bot Token: {telegram['bot_token'][:20]}...")
        print(f"Chat ID: {telegram['chat_id']}")
    else:
        print("\n⚠️  텔레그램 설정이 없습니다 (선택사항)")

    print("=" * 60)
