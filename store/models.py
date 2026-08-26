from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)

    def clean(self):
        if not self.nombre or not self.nombre.strip():
            raise ValidationError("El nombre del cliente es obligatorio.")

    def __str__(self):
        return self.nombre


class DireccionEnvio(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="direcciones"
    )
    calle = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20)

    def clean(self):
        if not self.calle or not self.calle.strip():
            raise ValidationError("La calle es obligatoria.")
        if not self.ciudad or not self.ciudad.strip():
            raise ValidationError("La ciudad es obligatoria.")

    def __str__(self):
        return f"{self.calle}, {self.ciudad}"


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    activo = models.BooleanField(default=True)

    def clean(self):
        if self.precio is not None and self.precio <= 0:
            raise ValidationError("El precio del producto debe ser mayor que cero.")

    def __str__(self):
        return self.nombre


class Talla(models.Model):
    TALLAS_DISPONIBLES = [
        ("XS", "XS"),
        ("S", "S"),
        ("M", "M"),
        ("L", "L"),
        ("XL", "XL"),
        ("XXL", "XXL"),
    ]

    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="tallas"
    )
    talla = models.CharField(max_length=5, choices=TALLAS_DISPONIBLES)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("producto", "talla")

    def tiene_stock(self, cantidad):
        return self.stock >= cantidad

    def clean(self):
        if self.stock is not None and self.stock < 0:
            raise ValidationError("El stock no puede ser negativo.")

    def __str__(self):
        return f"{self.producto.nombre} - {self.talla} ({self.stock} und.)"


class Pedido(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("CONFIRMADO", "Confirmado"),
        ("CANCELADO", "Cancelado"),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="pedidos"
    )
    direccion_envio = models.ForeignKey(
        DireccionEnvio, on_delete=models.PROTECT, related_name="pedidos"
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def calcular_total(self):
        subtotal = sum((item.subtotal() for item in self.items.all()), Decimal("0.00"))
        self.total = subtotal + self.costo_envio
        return self.total

    def clean(self):
        if self.total is not None and self.total < 0:
            raise ValidationError("El total del pedido no puede ser negativo.")

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente.nombre}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    talla = models.ForeignKey(
        Talla, on_delete=models.PROTECT, related_name="items_pedido"
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def clean(self):
        if self.cantidad is not None and self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor que cero.")
        if self.talla_id and self.cantidad and not self.talla.tiene_stock(self.cantidad):
            raise ValidationError(
                f"No hay stock suficiente de la talla {self.talla.talla}. "
                f"Disponible: {self.talla.stock}."
            )

    def __str__(self):
        return f"{self.cantidad} x {self.talla}"
