from django.test import TestCase
from django.test import Client
import json

from .domain.pedido_builder import PedidoBuilder
from .services import CheckoutService
from .models import Pedido, Producto, ItemPedido
from .infra.notification_interface import NotificationService
from .domain.excepciones import RecursoNoEncontradoError, ConflictoInventarioError


class MockNotificationForTest(NotificationService):
    def __init__(self):
        self.enviado = False
        self.cliente_destino = None

    def enviar_confirmacion(self, cliente):
        self.enviado = True
        self.cliente_destino = cliente


class Capa1DominioTests(TestCase):
    def setUp(self):
        self.producto_1 = Producto.objects.create(nombre="Laptop", precio="1000.00", stock=5)
        self.producto_2 = Producto.objects.create(nombre="Mouse", precio="50.00", stock=10)

    def test_creacion_pedido_exitoso(self):
        pedido, items = (
            PedidoBuilder()
            .set_cliente("Juan")
            .set_direccion("Calle 123")
            .add_item(self.producto_1, 1)
            .add_item(self.producto_2, 2)
            .build()
        )
        self.assertEqual(pedido.cliente, "Juan")
        self.assertEqual(pedido.total, 1100.00)
        self.assertEqual(len(items), 2)

    def test_falla_sin_items(self):
        with self.assertRaisesMessage(ValueError, "El pedido debe contener al menos un ítem."):
            PedidoBuilder().set_cliente("Juan").set_direccion("Calle 123").build()

    def test_falla_sin_stock(self):
        with self.assertRaises(ConflictoInventarioError):
            PedidoBuilder().set_cliente("Juan").set_direccion("Calle 123").add_item(self.producto_1, 10).build()


class Capa2AplicacionTests(TestCase):
    def setUp(self):
        self.producto_1 = Producto.objects.create(nombre="Laptop", precio="1000.00", stock=5)
        self.mock_notification = MockNotificationForTest()
        self.servicio = CheckoutService(self.mock_notification)

    def test_servicio_procesar_compra_exito(self):
        items_data = [{"producto_id": self.producto_1.id, "cantidad": 2}]
        pedido = self.servicio.procesar_compra("Ana", "Avenida 456", items_data)

        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(ItemPedido.objects.count(), 1)
        self.assertTrue(self.mock_notification.enviado)
        
        # Verificar descuento de stock
        self.producto_1.refresh_from_db()
        self.assertEqual(self.producto_1.stock, 3)

    def test_servicio_falla_producto_no_existe(self):
        items_data = [{"producto_id": 999, "cantidad": 1}]
        with self.assertRaises(RecursoNoEncontradoError):
            self.servicio.procesar_compra("Ana", "Avenida 456", items_data)

    def test_servicio_falla_sin_stock(self):
        items_data = [{"producto_id": self.producto_1.id, "cantidad": 10}]
        with self.assertRaises(ConflictoInventarioError):
            self.servicio.procesar_compra("Ana", "Avenida 456", items_data)
        
        # Transacción revertida
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertFalse(self.mock_notification.enviado)


class VistaHTTPTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.producto = Producto.objects.create(nombre="Teclado", precio="100.00", stock=5)

    def test_endpoint_checkout_exito_201(self):
        payload = {
            'cliente': 'Carlos',
            'direccion': 'Plaza Central',
            'items': [{'producto_id': self.producto.id, 'cantidad': 1}]
        }
        response = self.client.post('/checkout/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_endpoint_checkout_400(self):
        payload = {
            'cliente': 'Carlos',
            'direccion': 'Plaza',
            # Falta items, DRF debe rechazar
        }
        response = self.client.post('/checkout/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_endpoint_checkout_404(self):
        payload = {
            'cliente': 'Carlos',
            'direccion': 'Plaza',
            'items': [{'producto_id': 999, 'cantidad': 1}]
        }
        response = self.client.post('/checkout/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_endpoint_checkout_409(self):
        payload = {
            'cliente': 'Carlos',
            'direccion': 'Plaza',
            'items': [{'producto_id': self.producto.id, 'cantidad': 10}]
        }
        response = self.client.post('/checkout/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 409)
