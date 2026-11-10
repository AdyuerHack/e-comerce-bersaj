from decimal import Decimal

from ..exceptions import (
    RecursoNoEncontradoError,
    ConflictoInventarioError,
)
from store.infra.catalog_client import CatalogGatewayFactory
from store.models import Pedido

COSTO_ENVIO_BASE = Decimal("8000.00")


class PedidoBuilder:
    """Construye un Pedido paso a paso, validando reglas de negocio antes
    de permitir su persistencia (.build()). Soporta desacoplamiento mediante
    CatalogGateway (Strangler Pattern)."""

    def __init__(self, catalog_gateway=None):
        self.catalog_gateway = catalog_gateway or CatalogGatewayFactory.get_gateway()
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
        info = self.catalog_gateway.obtener_talla_info(talla_id)

        if info["stock"] < cantidad:
            nombre = info.get("producto_nombre", "Producto")
            raise ConflictoInventarioError(
                f"Stock insuficiente para {nombre} - {info['talla']}. Disponible: {info['stock']}."
            )

        self._items_data.append((info, cantidad))
        return self

    def agregar_prendas(self, items):
        for item in items:
            self.agregar_prenda(item["talla_id"], item["cantidad"])
        return self

    def calcular_envio_y_total(self):
        subtotal = sum(
            (item_info["precio"] * cantidad for item_info, cantidad in self._items_data),
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
