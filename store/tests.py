import json
from decimal import Decimal

from django.test import Client, TestCase

from .models import Cliente, DireccionEnvio, Producto, Talla


class CheckoutViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.cliente = Cliente.objects.create(
            nombre="Ana Gomez", email="ana@example.com", telefono="3001234567"
        )
        self.direccion = DireccionEnvio.objects.create(
            cliente=self.cliente,
            calle="Cra 45 #10-20",
            ciudad="Medellin",
            codigo_postal="050001",
        )
        self.producto = Producto.objects.create(
            nombre="Camiseta Basica", precio=Decimal("45000.00")
        )
        self.talla = Talla.objects.create(
            producto=self.producto, talla="M", stock=5
        )

    def _post(self, payload_dict):
        return self.client.post(
            "/checkout/",
            data=json.dumps(payload_dict),
            content_type="application/json",
        )

    def test_compra_valida_descuenta_stock_y_suma_envio(self):
        payload = {
            "cliente_id": self.cliente.id,
            "direccion_id": self.direccion.id,
            "items": [{"talla_id": self.talla.id, "cantidad": 1}],
        }
        response = self._post(payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["total"], "53000.00")  # 45000 + 8000 envio

        self.talla.refresh_from_db()
        self.assertEqual(self.talla.stock, 4)

    def test_stock_insuficiente_devuelve_409(self):
        payload = {
            "cliente_id": self.cliente.id,
            "direccion_id": self.direccion.id,
            "items": [{"talla_id": self.talla.id, "cantidad": 999}],
        }
        response = self._post(payload)

        self.assertEqual(response.status_code, 409)
        self.assertIn("Stock insuficiente", response.json()["error"])

        self.talla.refresh_from_db()
        self.assertEqual(self.talla.stock, 5)  # no debe descontar nada

    def test_talla_inexistente_devuelve_404(self):
        payload = {
            "cliente_id": self.cliente.id,
            "direccion_id": self.direccion.id,
            "items": [{"talla_id": 9999, "cantidad": 1}],
        }
        response = self._post(payload)

        self.assertEqual(response.status_code, 404)
        self.assertIn("no existe", response.json()["error"])

    def test_cliente_inexistente_devuelve_404(self):
        payload = {
            "cliente_id": 9999,
            "direccion_id": self.direccion.id,
            "items": [{"talla_id": self.talla.id, "cantidad": 1}],
        }
        response = self._post(payload)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Cliente no encontrado.")

    def test_direccion_inexistente_devuelve_404(self):
        payload = {
            "cliente_id": self.cliente.id,
            "direccion_id": 9999,
            "items": [{"talla_id": self.talla.id, "cantidad": 1}],
        }
        response = self._post(payload)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"],
            "Dirección de envío no encontrada para este cliente.",
        )

    def test_campos_faltantes_devuelve_400(self):
        response = self._post({"cliente_id": self.cliente.id})

        self.assertEqual(response.status_code, 400)
        self.assertIn("direccion_id", response.json())
        self.assertIn("items", response.json())

    def test_json_invalido_devuelve_400(self):
        response = self.client.post(
            "/checkout/", data="{esto no es json", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)

    def test_strangler_pattern_con_microservicio_exitoso(self):
        from unittest.mock import patch, MagicMock
        from .infra.catalog_client import HttpCatalogMicroserviceAdapter
        from .services import CheckoutService
        from .infra.mock_email_service import MockEmailService

        adapter = HttpCatalogMicroserviceAdapter(base_url="http://fake-catalog")

        with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "id": self.talla.id,
                    "talla": "M",
                    "stock": 10,
                    "producto_id": self.producto.id,
                    "producto_nombre": "Camiseta Mock",
                    "precio": 45000.00,
                },
            )
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"success": True, "message": "Stock descontado"},
            )

            service = CheckoutService(
                notification_service=MockEmailService(),
                catalog_gateway=adapter,
            )

            payload = {
                "cliente_id": self.cliente.id,
                "direccion_id": self.direccion.id,
                "items": [{"talla_id": self.talla.id, "cantidad": 2}],
            }

            resultado = service.procesar_compra(payload)
            self.assertEqual(resultado["mensaje"], "Compra realizada correctamente")
            self.assertEqual(resultado["total"], "98000.00")  # (45000*2) + 8000
            self.assertTrue(mock_get.called)
            self.assertTrue(mock_post.called)


class AdapterPatternTests(TestCase):
    """Pruebas del Patrón Adapter (Inversión de Dependencias - DIP) para API de Terceros."""

    def test_mock_exchange_rate_adapter(self):
        from .infra.adapters.mock_exchange_adapter import MockExchangeRateAdapter
        adapter = MockExchangeRateAdapter(fixed_rate=Decimal("4000.00"))
        
        tasa = adapter.obtener_tasa_usd_a_cop()
        self.assertEqual(tasa, Decimal("4000.00"))

        monto_cop = Decimal("40000.00")
        monto_usd = adapter.convertir_cop_a_usd(monto_cop)
        self.assertEqual(monto_usd, Decimal("10.00"))

    def test_open_exchange_adapter_con_fallback(self):
        from unittest.mock import patch
        from .infra.adapters.open_exchange_adapter import OpenExchangeRateAdapter
        import requests

        adapter = OpenExchangeRateAdapter()
        with patch("requests.get", side_effect=requests.RequestException("Network down")):
            tasa = adapter.obtener_tasa_usd_a_cop()
            self.assertEqual(tasa, Decimal("4200.00"))  # Fallback resiliente


class AllyServiceClientTests(TestCase):
    """Pruebas para el consumo del servicio provisto por el equipo aliado."""

    def test_ally_service_fallback(self):
        from .infra.ally_service_client import AllyServiceClient
        client = AllyServiceClient(base_url="")
        res = client.obtener_catalogo_aliado()
        self.assertFalse(res["conectado"])
        self.assertIn("productos", res["datos"])


class CeleryAsynchronousTaskTests(TestCase):
    """Pruebas de tareas en segundo plano (Celery & Redis)."""

    def test_tarea_confirmacion_asincrona(self):
        from .tasks import enviar_confirmacion_asincrona
        resultado = enviar_confirmacion_asincrona("Juan Perez", pedido_id=42, total="50000.00")
        self.assertEqual(resultado["status"], "ENVIADO")
        self.assertEqual(resultado["pedido_id"], 42)


class UIViewIntegrationTests(TestCase):
    """Pruebas de navegación UI, usabilidad y renderizado."""

    def setUp(self):
        self.client = Client()
        self.cliente = Cliente.objects.create(nombre="Carlos Gomez", email="carlos@example.com")
        self.producto = Producto.objects.create(nombre="Jean Bersaj", precio=Decimal("80000.00"))
        self.talla = Talla.objects.create(producto=self.producto, talla="32", stock=10)

    def test_catalogo_view_status_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jean Bersaj")

    def test_aliado_view_status_200(self):
        response = self.client.get("/tienda/aliado/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Servicios del Aliado")

    def test_catalog_gateway_listar_productos_y_tallas(self):
        from .infra.catalog_client import LocalCatalogAdapter
        adapter = LocalCatalogAdapter()
        productos = adapter.listar_productos()
        self.assertGreaterEqual(len(productos), 1)
        self.assertEqual(productos[0]["nombre"], "Jean Bersaj")

        tallas = adapter.listar_tallas_disponibles()
        self.assertGreaterEqual(len(tallas), 1)
        self.assertEqual(tallas[0]["stock"], 10)

    def test_compra_con_excepcion_rollback_atomico(self):
        from unittest.mock import MagicMock
        from .services import CheckoutService
        from .exceptions import ConflictoInventarioError
        from .models import Pedido

        mock_gateway = MagicMock()
        mock_gateway.obtener_talla_info.return_value = {
            "talla_id": self.talla.id,
            "talla": "32",
            "stock": 10,
            "producto_id": self.producto.id,
            "producto_nombre": "Jean Bersaj",
            "precio": Decimal("80000.00"),
        }
        mock_gateway.descontar_stock.side_effect = ConflictoInventarioError("Fallo simulado en microservicio")

        mock_notification = MagicMock()
        service = CheckoutService(notification_service=mock_notification, catalog_gateway=mock_gateway)

        payload = {
            "cliente_id": self.cliente.id,
            "direccion_id": DireccionEnvio.objects.create(cliente=self.cliente, calle="Cll 10", ciudad="Medellin", codigo_postal="05001").id,
            "items": [{"talla_id": self.talla.id, "cantidad": 1}],
        }

        pedidos_antes = Pedido.objects.count()
        with self.assertRaises(ConflictoInventarioError):
            service.procesar_compra(payload)

        # Debe haberse hecho rollback completo de la transacción
        self.assertEqual(Pedido.objects.count(), pedidos_antes)


