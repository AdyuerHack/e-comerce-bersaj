from .domain.pedido_builder import PedidoBuilder


class CheckoutService:

    def __init__(self, notification_service):
        self.notification_service = notification_service

    def procesar_compra(self, request):

        cliente = request.POST.get("cliente")
        direccion = request.POST.get("direccion")
        total = request.POST.get("total")
        if not cliente or not direccion or not total:
            return {"error": "Todos los campos son obligatorios"}

        pedido = (
            PedidoBuilder()
            .set_cliente(cliente)
            .set_direccion(direccion)
            .set_total(total)
            .build()
        )

        pedido.save()

        self.notification_service.enviar_confirmacion(cliente)

        return {
            "mensaje": "Compra realizada correctamente"
        }