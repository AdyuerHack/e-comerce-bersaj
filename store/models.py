from django.db import models

class Pedido(models.Model):
    cliente = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.cliente