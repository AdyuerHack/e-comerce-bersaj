from abc import ABC, abstractmethod

class NotificationService(ABC):

    @abstractmethod
    def enviar_confirmacion(self, cliente):
        pass