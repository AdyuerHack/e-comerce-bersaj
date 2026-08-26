from django.db import transaction

from .domain.pedido_builder import PedidoBuilder
from .domain.excepciones import RecursoNoEncontradoError
from .models import Producto


class CheckoutService:

    def __init__(self, notification_service):
        self.notification_service = notification_service

    def procesar_compra(self, cliente: str, direccion: str, items_data: list):
        """
        Orquesta el flujo de creación de un pedido.
        items_data formato esperado: [{"producto_id": 1, "cantidad": 2}, ...]
        """
        builder = PedidoBuilder().set_cliente(cliente).set_direccion(direccion)

        # 1. Búsqueda y Validación de ítems
        for item_data in items_data:
            producto_id = item_data.get('producto_id')
            cantidad = item_data.get('cantidad', 0)

            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                raise RecursoNoEncontradoError(f"El producto con ID {producto_id} no existe.")

            # Esto puede lanzar ValueError (cant <= 0) o ConflictoInventarioError (sin stock)
            builder.add_item(producto, cantidad)

        # 2. Construcción de la entidad raíz y sus hijos
        pedido, items = builder.build()

        # 3. Persistencia Atómica (si algo falla, se revierte)
        with transaction.atomic():
            pedido.save()
            for item in items:
                item.pedido = pedido # Vinculamos el hijo al padre
                item.save()
                
                # Descontar stock
                item.producto.stock -= item.cantidad
                item.producto.save()

        # 4. Infraestructura (Notificaciones externas)
        self.notification_service.enviar_confirmacion(cliente)

        # 5. Retornamos la entidad pura
        return pedido