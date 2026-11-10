from decimal import Decimal
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils.translation import gettext as _

from .models import Cliente, DireccionEnvio, Talla, Producto
from .services import CheckoutService
from .infra.factory import NotificationFactory
from .infra.catalog_client import CatalogGatewayFactory
from .infra.adapters.factory import CurrencyAdapterFactory
from .infra.ally_service_client import AllyServiceClient
from .exceptions import RecursoNoEncontradoError, ConflictoInventarioError


class CatalogoView(View):
    """Vista de catálogo con conversión internacional vía Patrón Adapter (Terceros)."""

    def get(self, request):
        adapter = CurrencyAdapterFactory.get_adapter()
        tasa_usd = adapter.obtener_tasa_usd_a_cop()

        # Obtener productos (vía local o microservicio)
        productos_db = Producto.objects.filter(activo=True).prefetch_related("tallas")
        productos = []

        for p in productos_db:
            precio_usd = adapter.convertir_cop_a_usd(p.precio)
            tallas = [{"id": t.id, "talla": t.talla, "stock": t.stock} for t in p.tallas.all()]
            productos.append({
                "id": p.id,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "precio": p.precio,
                "precio_usd": str(precio_usd),
                "categoria": "Moda Bersaj",
                "tallas": tallas,
            })

        context = {
            "productos": productos,
            "tasa_usd": str(tasa_usd),
        }
        return render(request, "catalog.html", context)


class CheckoutUIView(View):
    """Vista interactiva de Checkout con formularios robustos y validaciones de usabilidad."""

    def get(self, request):
        clientes = Cliente.objects.all()
        direcciones = DireccionEnvio.objects.select_related("cliente").all()
        tallas_db = Talla.objects.select_related("producto").filter(stock__gt=0)
        
        tallas = [
            {
                "id": t.id,
                "talla": t.talla,
                "stock": t.stock,
                "producto_nombre": t.producto.nombre,
                "precio": t.producto.precio,
            }
            for t in tallas_db
        ]

        adapter = CurrencyAdapterFactory.get_adapter()
        tasa_usd = adapter.obtener_tasa_usd_a_cop()

        context = {
            "clientes": clientes,
            "direcciones": direcciones,
            "tallas": tallas,
            "tasa_usd": str(tasa_usd),
        }
        return render(request, "checkout.html", context)

    def post(self, request):
        cliente_id = request.POST.get("cliente_id")
        direccion_id = request.POST.get("direccion_id")
        talla_id = request.POST.get("talla_id")
        cantidad = int(request.POST.get("cantidad", 1))

        if not all([cliente_id, direccion_id, talla_id]):
            messages.error(request, _("Todos los campos del formulario son obligatorios."))
            return redirect("tienda_checkout")

        payload = {
            "cliente_id": int(cliente_id),
            "direccion_id": int(direccion_id),
            "items": [{"talla_id": int(talla_id), "cantidad": cantidad}],
        }

        notification = NotificationFactory.create()
        service = CheckoutService(notification)

        try:
            resultado = service.procesar_compra(payload)
            if "error" in resultado:
                messages.error(request, _(resultado["error"]))
                return redirect("tienda_checkout")

            return render(request, "order_success.html", {"resultado": resultado})

        except (RecursoNoEncontradoError, ConflictoInventarioError) as e:
            messages.error(request, _(str(e)))
            return redirect("tienda_checkout")
        except Exception as e:
            messages.error(request, f"Error inesperado: {str(e)}")
            return redirect("tienda_checkout")


class AliadoView(View):
    """Vista para mostrar el servicio consumido del equipo aliado (Requerimiento 2.3)."""

    def get(self, request):
        client = AllyServiceClient()
        aliado_info = client.obtener_catalogo_aliado()

        adapter = CurrencyAdapterFactory.get_adapter()
        tasa_usd = adapter.obtener_tasa_usd_a_cop()

        return render(
            request,
            "ally.html",
            {
                "aliado": aliado_info,
                "tasa_usd": str(tasa_usd),
            },
        )
