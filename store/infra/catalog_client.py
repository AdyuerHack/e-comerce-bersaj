import os
import requests
from abc import ABC, abstractmethod
from decimal import Decimal

from ..exceptions import (
    RecursoNoEncontradoError,
    ConflictoInventarioError,
)


class CatalogGateway(ABC):
    """Interfaz para acceder al catálogo e inventario, desacoplando
    la implementación monolítica de la arquitectura de microservicios."""

    @abstractmethod
    def obtener_talla_info(self, talla_id):
        pass

    @abstractmethod
    def descontar_stock(self, items):
        pass


class LocalCatalogAdapter(CatalogGateway):
    """Implementación de respaldo que consulta los modelos locales de Django."""

    def obtener_talla_info(self, talla_id):
        from store.models import Talla
        try:
            talla = Talla.objects.select_related("producto").get(pk=talla_id)
            return {
                "talla_id": talla.id,
                "talla": talla.talla,
                "stock": talla.stock,
                "producto_id": talla.producto.id,
                "producto_nombre": talla.producto.nombre,
                "precio": talla.producto.precio,
                "objeto_modelo": talla,
            }
        except Talla.DoesNotExist:
            raise RecursoNoEncontradoError(f"La talla con id {talla_id} no existe.")

    def descontar_stock(self, items):
        from store.models import Talla
        for talla_id, cantidad in items:
            talla = Talla.objects.get(pk=talla_id)
            if talla.stock < cantidad:
                raise ConflictoInventarioError(
                    f"Stock insuficiente para {talla}. Disponible: {talla.stock}."
                )
            talla.stock -= cantidad
            talla.save()


class HttpCatalogMicroserviceAdapter(CatalogGateway):
    """Implementación del Strangler Pattern que redirige las llamadas
    hacia el microservicio independiente en Flask vía HTTP/REST."""

    def __init__(self, base_url=None):
        self.base_url = (base_url or os.getenv("CATALOG_SERVICE_URL", "http://localhost:5001")).rstrip("/")

    def obtener_talla_info(self, talla_id):
        url = f"{self.base_url}/api/v1/tallas/{talla_id}"
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 404:
                raise RecursoNoEncontradoError(f"La talla con id {talla_id} no existe.")
            resp.raise_for_status()
            data = resp.json()
            data["talla_id"] = data.get("talla_id") or data.get("id")
            data["precio"] = Decimal(str(data["precio"]))
            return data
        except requests.RequestException as e:
            if isinstance(e, requests.HTTPError) and e.response.status_code == 404:
                raise RecursoNoEncontradoError(f"La talla con id {talla_id} no existe.")
            raise RuntimeError(f"Error comunicando con microservicio de catálogo: {str(e)}")

    def descontar_stock(self, items):
        url = f"{self.base_url}/api/v1/inventory/decrease"
        payload = {"items": [{"talla_id": tid, "cantidad": qty} for tid, qty in items]}
        try:
            resp = requests.post(url, json=payload, timeout=3)
            if resp.status_code == 404:
                raise RecursoNoEncontradoError(resp.json().get("error", "Talla no encontrada"))
            if resp.status_code == 409:
                raise ConflictoInventarioError(resp.json().get("error", "Stock insuficiente"))
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                if e.response.status_code == 409:
                    raise ConflictoInventarioError(e.response.json().get("error", "Stock insuficiente"))
                if e.response.status_code == 404:
                    raise RecursoNoEncontradoError(e.response.json().get("error", "Recurso no encontrado"))
            raise RuntimeError(f"Falla de comunicación con microservicio de inventario: {str(e)}")


class CatalogGatewayFactory:
    """Factory para decidir en tiempo de ejecución si se usa el microservicio
    Flask (Strangler Fig) o el fallback local."""

    @staticmethod
    def get_gateway() -> CatalogGateway:
        use_microservice = os.getenv("USE_CATALOG_MICROSERVICE", "false").lower() in ("true", "1", "yes")
        if use_microservice:
            return HttpCatalogMicroserviceAdapter()
        return LocalCatalogAdapter()
