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