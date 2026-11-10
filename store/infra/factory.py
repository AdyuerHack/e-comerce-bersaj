import os

from .email_service import EmailService
from .mock_email_service import MockEmailService
from .async_email_service import AsyncCeleryNotificationService


class NotificationFactory:

    @staticmethod
    def create():
        modo = os.getenv("EMAIL_MODE", "MOCK").upper()

        if modo in ("CELERY", "ASYNC"):
            return AsyncCeleryNotificationService()

        if modo == "REAL":
            return EmailService()

        return MockEmailService()

    