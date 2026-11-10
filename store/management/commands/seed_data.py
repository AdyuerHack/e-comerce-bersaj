from decimal import Decimal
from django.core.management.base import BaseCommand
from store.models import Cliente, DireccionEnvio, Producto, Talla


class Command(BaseCommand):
    help = "Pobla la base de datos con datos de prueba iniciales para la tienda Bersaj."

    def handle(self, *args, **options):
        # 1. Clientes
        c1, _ = Cliente.objects.get_or_create(
            email="ana.gomez@example.com",
            defaults={"nombre": "Ana Gómez", "telefono": "3001234567"},
        )
        c2, _ = Cliente.objects.get_or_create(
            email="carlos.perez@example.com",
            defaults={"nombre": "Carlos Pérez", "telefono": "3109876543"},
        )
        c3, _ = Cliente.objects.get_or_create(
            email="maria.rodriguez@example.com",
            defaults={"nombre": "María Rodríguez", "telefono": "3154567890"},
        )

        # 2. Direcciones
        DireccionEnvio.objects.get_or_create(
            cliente=c1,
            calle="Carrera 43A #1-50",
            ciudad="Medellín",
            codigo_postal="050021",
        )
        DireccionEnvio.objects.get_or_create(
            cliente=c2,
            calle="Calle 72 #10-34",
            ciudad="Bogotá",
            codigo_postal="110221",
        )
        DireccionEnvio.objects.get_or_create(
            cliente=c3,
            calle="Avenida San Martín #8-12",
            ciudad="Cartagena",
            codigo_postal="130001",
        )

        # 3. Productos y Tallas
        p1, _ = Producto.objects.get_or_create(
            nombre="Camiseta Básica Oversize",
            defaults={
                "descripcion": "Algodón 100% peinado de alta densidad.",
                "precio": Decimal("45000.00"),
                "activo": True,
            },
        )
        Talla.objects.get_or_create(producto=p1, talla="S", defaults={"stock": 10})
        Talla.objects.get_or_create(producto=p1, talla="M", defaults={"stock": 15})
        Talla.objects.get_or_create(producto=p1, talla="L", defaults={"stock": 8})

        p2, _ = Producto.objects.get_or_create(
            nombre="Pantalón Cargo Denim",
            defaults={
                "descripcion": "Jeans estilo cargo corte relajado con múltiples bolsillos.",
                "precio": Decimal("110000.00"),
                "activo": True,
            },
        )
        Talla.objects.get_or_create(producto=p2, talla="30", defaults={"stock": 5})
        Talla.objects.get_or_create(producto=p2, talla="32", defaults={"stock": 12})
        Talla.objects.get_or_create(producto=p2, talla="34", defaults={"stock": 6})

        p3, _ = Producto.objects.get_or_create(
            nombre="Chaqueta Bomber Bersaj",
            defaults={
                "descripcion": "Chaqueta impermeable con forro térmico y cierre metálico.",
                "precio": Decimal("160000.00"),
                "activo": True,
            },
        )
        Talla.objects.get_or_create(producto=p3, talla="M", defaults={"stock": 4})
        Talla.objects.get_or_create(producto=p3, talla="L", defaults={"stock": 7})

        self.stdout.write(self.style.SUCCESS("Datos de prueba inicializados correctamente."))

