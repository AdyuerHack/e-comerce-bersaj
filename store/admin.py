from django.contrib import admin

from .models import Cliente, DireccionEnvio, ItemPedido, Pedido, Producto, Talla


class TallaInline(admin.TabularInline):
    model = Talla
    extra = 1


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email", "telefono")


@admin.register(DireccionEnvio)
class DireccionEnvioAdmin(admin.ModelAdmin):
    list_display = ("cliente", "calle", "ciudad", "codigo_postal")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "activo")
    inlines = [TallaInline]


@admin.register(Talla)
class TallaAdmin(admin.ModelAdmin):
    list_display = ("producto", "talla", "stock")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "total", "estado", "fecha_creacion")
    inlines = [ItemPedidoInline]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "talla", "cantidad", "precio_unitario")
