import os

from .email_service import EmailService
from .mock_email_service import MockEmailService


class NotificationFactory:

    @staticmethod
    def create():

        modo = os.getenv("EMAIL_MODE", "MOCK")

        if modo == "REAL":
            return EmailService()

        return MockEmailService()
    