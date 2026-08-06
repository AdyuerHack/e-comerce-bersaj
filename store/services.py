from .domain.pedido_builder import PedidoBuilder


class CheckoutService:

    def __init__(self, notification_service):
        self.notification_service = notification_service

    def procesar_compra(self, request):

        cliente = request.POST.get("cliente")
        direccion = request.POST.get("direccion")
        total = request.POST.get("total")
        try:
            pedido = (
                PedidoBuilder()
                .set_cliente(cliente)
                .set_direccion(direccion)
                .set_total(total)
                .build()
            )
        except ValueError as e:
            return {"error": str(e)}

        pedido.save()

        self.notification_service.enviar_confirmacion(cliente)

        return {
            "mensaje": "Compra realizada correctamente"
        }