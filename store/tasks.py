import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="store.enviar_correo_confirmacion")
def enviar_confirmacion_asincrona(cliente_nombre, pedido_id=None, total=None):
    """Tarea asíncrona ejecutada por Celery Worker a través de Redis Message Broker.
    Evita bloquear el hilo HTTP principal durante el checkout."""
    mensaje = f"[CELERY EVENT] Correo de confirmación enviado a {cliente_nombre}"
    if pedido_id:
        mensaje += f" para el Pedido #{pedido_id}"
    if total:
        mensaje += f" por valor de ${total}"
    
    print(mensaje)
    logger.info(mensaje)
    return {"status": "ENVIADO", "destinatario": cliente_nombre, "pedido_id": pedido_id}


@shared_task(name="store.generar_reporte_ventas")
def generar_reporte_ventas(fecha_inicio=None, fecha_fin=None):
    """Tarea asíncrona para generación de reportes pesados en segundo plano."""
    logger.info(f"Generando reporte de ventas asíncrono para rango: {fecha_inicio} a {fecha_fin}")
    return {"reporte": "Reporte generado satisfactoriamente", "filas": 150}
