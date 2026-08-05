from .notification_interface import NotificationService

class MockEmailService(NotificationService):

    def enviar_confirmacion(self, cliente):
        print(f"MOCK: correo enviado a {cliente}")