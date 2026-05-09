from app.core.logger import logger


def send_email(user_id: str, transaction_id: str, message: str) -> bool:
    logger.info(
        "email_notification_sent",
        user_id=user_id,
        transaction_id=transaction_id,
        message=message,
        channel="EMAIL",
    )
    return True
