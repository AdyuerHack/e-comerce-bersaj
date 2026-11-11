from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .infra.factory import NotificationFactory
from .services import CheckoutService
from .serializers import (
    CheckoutInputSerializer,
    CheckoutOutputSerializer,
)
from .exceptions import (
    RecursoNoEncontradoError,
    ConflictoInventarioError,
)


class CheckoutView(APIView):

    def post(self, request):
        serializer = CheckoutInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        datos = serializer.validated_data

        # 1. Extraemos los datos validados
        cliente = serializer.validated_data.get("cliente")
        direccion = serializer.validated_data.get("direccion")
        items_data = serializer.validated_data.get("items")

        # 2. Composition Root: Preparamos dependencias (Factory)
        notification = NotificationFactory.create()
        service = CheckoutService(notification)

        try:
            resultado = service.procesar_compra(datos)

        except RecursoNoEncontradoError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

        except ConflictoInventarioError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_409_CONFLICT
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        output_serializer = CheckoutOutputSerializer(resultado)

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
