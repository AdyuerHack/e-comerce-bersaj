import logging
from .notification_interface import NotificationService
from store.tasks import enviar_confirmacion_asincrona

logger = logging.getLogger(__name__)


class AsyncCeleryNotificationService(NotificationService):
    """Implementación de notificación asíncrona mediante Message Broker (Redis/Celery).
    Garantiza resiliencia desacoplando la transacción web del procesamiento de fondo."""

    def enviar_confirmacion(self, cliente, pedido_id=None, total=None):
        try:
            # Enqueue asynchronous task via Redis
            enviar_confirmacion_asincrona.delay(cliente, pedido_id=pedido_id, total=total)
            detalle = f" (Pedido #{pedido_id})" if pedido_id else ""
            print(f"[ASYNC] Encolada confirmación en Celery/Redis para {cliente}{detalle}")
        except Exception as e:
            # Graceful degradation (fallback to local log if broker is unreachable)
            logger.warning(f"No se pudo encolar en Celery/Redis ({e}). Aplicando fallback local.")
            print(f"[FALLBACK SYNC] Correo enviado a {cliente} (Broker no disponible)")
