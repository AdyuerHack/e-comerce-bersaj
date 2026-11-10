import os
import logging
import requests

logger = logging.getLogger(__name__)


class AllyServiceClient:
    """Cliente para consumir el servicio provisto por el equipo aliado (Requerimiento 2.3)."""

    def __init__(self, base_url=None, timeout=3):
        self.base_url = (base_url or os.getenv("ALLY_SERVICE_URL", "")).rstrip("/")
        self.timeout = timeout

    def obtener_catalogo_aliado(self):
        """Consulta el endpoint del equipo aliado.
        Si la URL no está configurada o el servicio del aliado está apagado,
        aplica resiliencia entregando una respuesta segura con advertencia."""
        if self.base_url:
            try:
                response = requests.get(f"{self.base_url}/api/v1/public/catalog", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "conectado": True,
                        "fuente": "Remoto (Equipo Aliado)",
                        "url": self.base_url,
                        "datos": data,
                    }
            except requests.RequestException as e:
                logger.warning(f"No se pudo contactar al equipo aliado en {self.base_url}: {e}")

        # Fallback resiliente / Datos simulados de integración
        return {
            "conectado": False,
            "fuente": "Integración Simulada (Esperando IP del Aliado)",
            "url": self.base_url or "http://aliado-ip:puerto",
            "datos": {
                "tienda": "Aliado Estratégico Moda & Accesorios",
                "descripcion": "Catálogo de calzado y accesorios complementarios",
                "productos": [
                    {
                        "id": 101,
                        "nombre": "Zapatillas Urbanas Canvas",
                        "precio": 185000.00,
                        "categoria": "Calzado",
                        "stock_total": 14,
                    },
                    {
                        "id": 102,
                        "nombre": "Gorra Clásica Bersaj Partner",
                        "precio": 45000.00,
                        "categoria": "Accesorios",
                        "stock_total": 22,
                    },
                ],
            },
        }
