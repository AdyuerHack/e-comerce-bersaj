# TODO (Capa 3): Importar APIView de rest_framework.views y serializers
from django.http import JsonResponse
from django.views import View
import json

from .infra.factory import NotificationFactory
from .services import CheckoutService
from .domain.excepciones import RecursoNoEncontradoError, ConflictoInventarioError


# TODO (Capa 3): Cambiar herencia de View a APIView de DRF
class CheckoutView(View):
    
    # TODO (Capa 3): Usar Request de DRF y validar con un Serializer
    def post(self, request):
        try:
            body = json.loads(request.body)
            cliente = body.get("cliente")
            direccion = body.get("direccion")
            items_data = body.get("items", [])
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        notification = NotificationFactory.create()
        service = CheckoutService(notification)

        try:
            # La Capa de Aplicación orquesta el negocio
            pedido = service.procesar_compra(cliente, direccion, items_data)
            return JsonResponse({
                "mensaje": "Compra realizada correctamente",
                "pedido_id": pedido.id,
                "total": str(pedido.total)
            }, status=201)
            
        except ValueError as e:
            # 400 Bad Request: Errores de validación (ej. cant < 0)
            return JsonResponse({"error": str(e)}, status=400)
            
        except RecursoNoEncontradoError as e:
            # 404 Not Found: El producto no existe
            return JsonResponse({"error": str(e)}, status=404)
            
        except ConflictoInventarioError as e:
            # 409 Conflict: Problemas de stock
            return JsonResponse({"error": str(e)}, status=409)