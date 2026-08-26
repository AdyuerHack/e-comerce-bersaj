from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .infra.factory import NotificationFactory
from .services import CheckoutService
from .domain.excepciones import RecursoNoEncontradoError, ConflictoInventarioError
from .serializers import CheckoutInputSerializer


class CheckoutView(APIView):
    
    def post(self, request):
        serializer = CheckoutInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 1. Extraemos los datos validados
        cliente = serializer.validated_data.get("cliente")
        direccion = serializer.validated_data.get("direccion")
        items_data = serializer.validated_data.get("items")

        # 2. Composition Root: Preparamos dependencias (Factory)
        notification = NotificationFactory.create()
        service = CheckoutService(notification)

        # 3. Ejecutamos el caso de uso
        try:
            # La Capa de Aplicación orquesta el negocio puro
            pedido = service.procesar_compra(cliente, direccion, items_data)
            return Response({
                "mensaje": "Compra realizada correctamente",
                "pedido_id": pedido.id,
                "total": str(pedido.total)
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            # 400 Bad Request: Errores de validación de negocio puro
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except RecursoNoEncontradoError as e:
            # 404 Not Found: El producto no existe
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            
        except ConflictoInventarioError as e:
            # 409 Conflict: Problemas de stock
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)