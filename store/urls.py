from django.urls import path

from .views import CheckoutView
from .views_ui import CatalogoView, CheckoutUIView, AliadoView

urlpatterns = [
    # Capa Web / Interfaz de Usuario (Usabilidad, i18n, Consumo Aliado)
    path("", CatalogoView.as_view(), name="tienda_catalogo"),
    path("tienda/checkout/", CheckoutUIView.as_view(), name="tienda_checkout"),
    path("tienda/aliado/", AliadoView.as_view(), name="tienda_aliado"),

    # Capa API REST
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("api/v1/checkout/", CheckoutView.as_view(), name="api_checkout"),
]
