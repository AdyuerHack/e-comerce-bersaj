from rest_framework import serializers

class ItemPedidoSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)

class CheckoutInputSerializer(serializers.Serializer):
    cliente = serializers.CharField(max_length=100)
    direccion = serializers.CharField(max_length=200)
    items = ItemPedidoSerializer(many=True, allow_empty=False)
