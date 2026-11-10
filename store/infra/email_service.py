from .notification_interface import NotificationService


class EmailService(NotificationService):

    def enviar_confirmacion(self, cliente, pedido_id=None, total=None):
        detalle = f" para el Pedido #{pedido_id}" if pedido_id else ""
        print(f"Correo REAL enviado a {cliente}{detalle}")
