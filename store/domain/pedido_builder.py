from store.models import Pedido, ItemPedido
from store.domain.excepciones import ConflictoInventarioError


class PedidoBuilder:

    def __init__(self):
        self.pedido = Pedido()
        self.items = []
        self._total = 0.0

    def set_cliente(self, cliente: str):
        self.pedido.cliente = cliente
        return self

    def set_direccion(self, direccion: str):
        self.pedido.direccion = direccion
        return self

    def add_item(self, producto, cantidad: int):
        if cantidad <= 0:
            raise ValueError(f"La cantidad para el producto {producto.nombre} debe ser mayor que 0.")
        
        if producto.stock < cantidad:
            raise ConflictoInventarioError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}, Solicitado: {cantidad}")

        # Calculamos subtotal
        subtotal = float(producto.precio) * cantidad
        self._total += subtotal

        # Preparamos el ítem (aún no se guarda en BD)
        item = ItemPedido(
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio
        )
        self.items.append(item)
        return self

    def build(self):
        if not self.pedido.cliente:
            raise ValueError("El cliente es obligatorio.")

        if not self.pedido.direccion:
            raise ValueError("La dirección es obligatoria.")

        if not self.items:
            raise ValueError("El pedido debe contener al menos un ítem.")

        self.pedido.total = self._total
        return self.pedido, self.items