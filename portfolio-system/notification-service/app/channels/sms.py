from app.core.logger import logger


def send_sms(user_id: str, transaction_id: str, message: str) -> bool:
    logger.info(
        "sms_notification_sent",
        user_id=user_id,
        transaction_id=transaction_id,
        message=message,
        channel="SMS",
    )
    return True
