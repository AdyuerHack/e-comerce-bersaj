from django.http import JsonResponse
from django.views import View

from .infra.factory import NotificationFactory
from .services import CheckoutService


class CheckoutView(View):

    def post(self, request):

        notification = NotificationFactory.create()

        service = CheckoutService(notification)

        return JsonResponse(service.procesar_compra(request))