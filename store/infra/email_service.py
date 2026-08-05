from .notification_interface import NotificationService

class EmailService(NotificationService):

    def enviar_confirmacion(self, cliente):
        print(f"Correo REAL enviado a {cliente}")