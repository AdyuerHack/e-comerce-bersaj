from store.models import Pedido


class PedidoBuilder:

    def __init__(self):
        self.pedido = Pedido()

    def set_cliente(self, cliente):
        self.pedido.cliente = cliente
        return self

    def set_direccion(self, direccion):
        self.pedido.direccion = direccion
        return self

    def set_total(self, total):
        self.pedido.total = total
        return self

    def build(self):

        if not self.pedido.cliente:
            raise ValueError("El cliente es obligatorio.")

        if not self.pedido.direccion:
            raise ValueError("La dirección es obligatoria.")

        if float(self.pedido.total) <= 0:
            raise ValueError("El total debe ser mayor que cero.")

        return self.pedido