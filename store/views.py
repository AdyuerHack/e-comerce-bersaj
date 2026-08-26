import json

from django.http import JsonResponse
from django.views import View

from .infra.factory import NotificationFactory
from .services import CheckoutService


class CheckoutView(View):

    def post(self, request):
        try:
            datos = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "El cuerpo de la petición debe ser JSON válido."}, status=400)

        notification = NotificationFactory.create()
        service = CheckoutService(notification)
        resultado = service.procesar_compra(datos)

        if "error" in resultado:
            return JsonResponse(resultado, status=400)

        return JsonResponse(resultado, status=201)