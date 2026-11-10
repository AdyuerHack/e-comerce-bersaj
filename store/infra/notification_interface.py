from abc import ABC, abstractmethod


class NotificationService(ABC):

    @abstractmethod
    def enviar_confirmacion(self, cliente, pedido_id=None, total=None):
        pass
