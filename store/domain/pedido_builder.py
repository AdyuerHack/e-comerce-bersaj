from decimal import Decimal

from ..exceptions import (
    RecursoNoEncontradoError,
    ConflictoInventarioError,
)

from store.models import Pedido, Talla

COSTO_ENVIO_BASE = Decimal("8000.00")


class PedidoBuilder:
    """Construye un Pedido paso a paso, validando reglas de negocio antes
    de permitir su persistencia (.build())."""

    def __init__(self):
        self.pedido = Pedido()
        self._items_data = []
        self._total = Decimal("0.00")

    def asignar_cliente(self, cliente):
        self.pedido.cliente = cliente
        return self

    def asignar_direccion(self, direccion):
        self.pedido.direccion_envio = direccion
        return self

    def agregar_prenda(self, talla_id, cantidad):
        try:
            talla = Talla.objects.select_related("producto").get(pk=talla_id)
        except Talla.DoesNotExist:
            raise RecursoNoEncontradoError(
                f"La talla con id {talla_id} no existe."
            )

        if not talla.tiene_stock(cantidad):
            raise ConflictoInventarioError(
                f"Stock insuficiente para {talla}. Disponible: {talla.stock}."
            )

        self._items_data.append((talla, cantidad))
        return self

    def agregar_prendas(self, items):
        for item in items:
            self.agregar_prenda(item["talla_id"], item["cantidad"])
        return self

    def calcular_envio_y_total(self):
        subtotal = sum(
            (talla.producto.precio * cantidad for talla, cantidad in self._items_data),
            Decimal("0.00"),
        )
        self._envio = COSTO_ENVIO_BASE if subtotal > 0 else Decimal("0.00")
        self._total = subtotal + self._envio
        return self

    def build(self):
        if not getattr(self.pedido, "cliente_id", None):
            raise ValueError("El cliente es obligatorio.")

        if not getattr(self.pedido, "direccion_envio_id", None):
            raise ValueError("La dirección de envío es obligatoria.")

        if not self._items_data:
            raise ValueError("El pedido debe tener al menos una prenda.")

        self.pedido.costo_envio = self._envio
        self.pedido.total = self._total
        self.pedido.full_clean()

        return self.pedido, self._items_data
