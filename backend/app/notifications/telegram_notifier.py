"""텔레그램 알림"""
import os
from telegram import Bot
from telegram.error import TelegramError
from loguru import logger


class TelegramNotifier:
    """텔레그램 알림 서비스"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = None

        if self.bot_token and self.chat_id:
            self.bot = Bot(token=self.bot_token)
            logger.info("Telegram bot initialized")
        else:
            logger.warning("Telegram credentials not configured")

    def send_message(self, message: str):
        """메시지 전송"""
        if not self.bot:
            logger.warning("Telegram bot not configured, skipping notification")
            return

        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Telegram message sent: {message[:50]}...")

        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")

    def send_availability_notification(self, camping_site: str, date: str):
        """예약 가능 알림"""
        message = f"""
🏕️ <b>예약 가능 알림</b>

캠핑장: {camping_site}
날짜: {date}

✅ 예약이 가능해졌습니다!
"""
        self.send_message(message)

    def send_reservation_success(self, camping_site: str, date: str, reservation_number: str = None):
        """예약 성공 알림"""
        message = f"""
✅ <b>예약 성공!</b>

캠핑장: {camping_site}
날짜: {date}
"""
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
