from django.db import transaction

from .domain.pedido_builder import PedidoBuilder
from .models import Cliente, DireccionEnvio, ItemPedido
from .exceptions import (
    RecursoNoEncontradoError,
    ConflictoInventarioError,
)
from .infra.catalog_client import CatalogGatewayFactory


class CheckoutService:

    def __init__(self, notification_service, catalog_gateway=None):
        self.notification_service = notification_service
        self.catalog_gateway = catalog_gateway or CatalogGatewayFactory.get_gateway()

    def procesar_compra(self, datos):
        cliente_id = datos.get("cliente_id")
        direccion_id = datos.get("direccion_id")
        items = datos.get("items", [])

        cliente = Cliente.objects.filter(pk=cliente_id).first()
        if cliente is None:
            raise RecursoNoEncontradoError("Cliente no encontrado.")

        direccion = DireccionEnvio.objects.filter(
            pk=direccion_id, cliente=cliente
        ).first()
        if direccion is None:
            raise RecursoNoEncontradoError("Dirección de envío no encontrada para este cliente.")

        builder = (
            PedidoBuilder(catalog_gateway=self.catalog_gateway)
            .asignar_cliente(cliente)
            .asignar_direccion(direccion)
            .agregar_prendas(items)
            .calcular_envio_y_total()
        )
        pedido, items_data = builder.build()

        with transaction.atomic():
            pedido.save()

            items_to_discount = []
            for item_info, cantidad in items_data:
                ItemPedido.objects.create(
                    pedido=pedido,
                    talla_id=item_info["talla_id"],
                    cantidad=cantidad,
                    precio_unitario=item_info["precio"],
                )
                items_to_discount.append((item_info["talla_id"], cantidad))

            # Atomic stock deduction via Gateway (Strangler Pattern)
            self.catalog_gateway.descontar_stock(items_to_discount)

            pedido.calcular_total()
            pedido.save()

        # Enviar confirmación enriquecida tolerante a fallos
        try:
            self.notification_service.enviar_confirmacion(
                cliente.nombre, pedido_id=pedido.pk, total=str(pedido.total)
            )
        except TypeError:
            self.notification_service.enviar_confirmacion(cliente.nombre)

        return {
            "mensaje": "Compra realizada correctamente",
            "pedido_id": pedido.pk,
            "total": str(pedido.total),
        }
