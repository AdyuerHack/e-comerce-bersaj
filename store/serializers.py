from rest_framework import serializers


class ItemPedidoSerializer(serializers.Serializer):
    talla_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)


class CheckoutInputSerializer(serializers.Serializer):
    cliente_id = serializers.IntegerField()
    direccion_id = serializers.IntegerField()
    items = ItemPedidoSerializer(many=True, allow_empty=False)


class CheckoutOutputSerializer(serializers.Serializer):
    mensaje = serializers.CharField()
    pedido_id = serializers.IntegerField()
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )