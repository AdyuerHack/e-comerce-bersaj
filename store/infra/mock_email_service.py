from .notification_interface import NotificationService


class MockEmailService(NotificationService):

    def enviar_confirmacion(self, cliente, pedido_id=None, total=None):
        print(f"MOCK: correo enviado a {cliente}")
