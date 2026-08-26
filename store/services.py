from .domain.pedido_builder import PedidoBuilder
from .models import Cliente, DireccionEnvio, ItemPedido


class CheckoutService:

    def __init__(self, notification_service):
        self.notification_service = notification_service

    def procesar_compra(self, datos):
        cliente_id = datos.get("cliente_id")
        direccion_id = datos.get("direccion_id")
        items = datos.get("items", [])

        cliente = Cliente.objects.filter(pk=cliente_id).first()
        if cliente is None:
            return {"error": "Cliente no encontrado."}

        direccion = DireccionEnvio.objects.filter(
            pk=direccion_id, cliente=cliente
        ).first()
        if direccion is None:
            return {"error": "Dirección de envío no encontrada para este cliente."}

        try:
            builder = (
                PedidoBuilder()
                .asignar_cliente(cliente)
                .asignar_direccion(direccion)
                .agregar_prendas(items)
                .calcular_envio_y_total()
            )
            pedido, items_data = builder.build()
        except ValueError as e:
            return {"error": str(e)}

        pedido.save()

        for talla, cantidad in items_data:
            ItemPedido.objects.create(
                pedido=pedido,
                talla=talla,
                cantidad=cantidad,
                precio_unitario=talla.producto.precio,
            )
            talla.stock -= cantidad
            talla.save()

        pedido.calcular_total()
        pedido.save()

        self.notification_service.enviar_confirmacion(cliente.nombre)

        return {
            "mensaje": "Compra realizada correctamente",
            "pedido_id": pedido.pk,
            "total": str(pedido.total),
        }
