"""텔레그램 알림"""
import os
import requests
from loguru import logger


class TelegramNotifier:
    """텔레그램 알림 서비스 (requests 기반 동기 방식)"""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Args:
            bot_token: 텔레그램 봇 토큰 (None이면 환경 변수에서 읽음)
            chat_id: 텔레그램 채팅 ID (None이면 환경 변수에서 읽음)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

        if self.bot_token and self.chat_id:
            logger.info("Telegram bot initialized")
        else:
            logger.warning("Telegram credentials not configured")

    def send_message(self, message: str) -> bool:
        """메시지 전송

        Returns:
            bool: 성공 여부
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot not configured, skipping notification")
            return False

        try:
            url = f"{self.api_base}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get('ok'):
                logger.info(f"Telegram message sent: {message[:50]}...")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                return False

        except requests.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_availability_notification(self, camping_site: str, date: str):
        """예약 가능 알림"""
        message = f"""
🏕️ <b>예약 가능 알림</b>

캠핑장: {camping_site}
날짜: {date}

✅ 예약이 가능해졌습니다!
"""
        self.send_message(message)

    def send_reservation_success(self, camping_site: str, date: str, reservation_number: str = None, seat_name: str = None):
        """예약 성공 알림"""
        message = f"""
✅ <b>예약 성공!</b>

캠핑장: {camping_site}
날짜: {date}
"""
        if seat_name:
            message += f"사이트: {seat_name}\n"
        if reservation_number:
            message += f"예약번호: {reservation_number}\n"

        message += "\n🎉 예약이 완료되었습니다!"

        self.send_message(message)

    def send_reservation_failure(self, camping_site: str, date: str, error: str):
        """예약 실패 알림"""
        message = f"""
❌ <b>예약 실패</b>

캠핑장: {camping_site}
날짜: {date}
오류: {error}

재시도가 필요합니다.
"""
        self.send_message(message)

    def send_cancellation_notification(self, camping_site: str, date: str):
        """취소 발생 알림"""
        message = f"""
🔔 <b>예약 취소 발생</b>

캠핑장: {camping_site}
날짜: {date}

예약이 취소되어 자리가 생겼습니다!
"""
        self.send_message(message)

    def send_error_notification(self, error: str):
        """에러 알림"""
        message = f"""
⚠️ <b>시스템 오류</b>

오류 내용: {error}

시스템 확인이 필요합니다.
"""
        self.send_message(message)

    def send_monitoring_start(self):
        """모니터링 시작 알림"""
        message = "🚀 <b>모니터링 시작</b>\n\n캠핑 예약 모니터링이 시작되었습니다."
        self.send_message(message)

    def send_monitoring_stop(self):
        """모니터링 중지 알림"""
        message = "⏹️ <b>모니터링 중지</b>\n\n캠핑 예약 모니터링이 중지되었습니다."
        self.send_message(message)
