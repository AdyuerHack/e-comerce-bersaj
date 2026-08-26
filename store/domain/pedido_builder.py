from decimal import Decimal
from store.models import Pedido, ItemPedido
from store.domain.excepciones import ConflictoInventarioError


class PedidoBuilder:

    def __init__(self):
        self.pedido = Pedido()
        self._productos_agrupados = {}
        self._total = Decimal('0.00')

    def set_cliente(self, cliente: str):
        self.pedido.cliente = cliente
        return self

    def set_direccion(self, direccion: str):
        self.pedido.direccion = direccion
        return self

    def add_item(self, producto, cantidad: int):
        if cantidad <= 0:
            raise ValueError(f"La cantidad para el producto {producto.nombre} debe ser mayor que 0.")
        
        # Agrupamos por producto para validar el stock real total solicitado
        if producto.id in self._productos_agrupados:
            self._productos_agrupados[producto.id]['cantidad'] += cantidad
        else:
            self._productos_agrupados[producto.id] = {
                'producto': producto,
                'cantidad': cantidad
            }
        
        return self

    def build(self):
        if not self.pedido.cliente:
            raise ValueError("El cliente es obligatorio.")

        if not self.pedido.direccion:
            raise ValueError("La dirección es obligatoria.")

        if not self._productos_agrupados:
            raise ValueError("El pedido debe contener al menos un ítem.")

        items_construidos = []
        
        for data in self._productos_agrupados.values():
            producto = data['producto']
            cantidad_total = data['cantidad']
            
            # Validación de stock agrupado (previene sobreventa por pedidos múltiples del mismo ítem)
            if producto.stock < cantidad_total:
                raise ConflictoInventarioError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}, Solicitado: {cantidad_total}")

            # Subtotal con Decimal
            subtotal = Decimal(str(producto.precio)) * cantidad_total
            self._total += subtotal

            item = ItemPedido(
                producto=producto,
                cantidad=cantidad_total,
                precio_unitario=producto.precio
            )
            items_construidos.append(item)

        self.pedido.total = self._total
        return self.pedido, items_construidos