from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from apps.mental.functions import get_alternativas_deportivas, get_flexibilidad_info, get_catalogo_actividades
import time
import logging


class MentalAnalysisView(APIView):
    def post(self, request):
        try:
            form_data = request.POST.dict()
            user_id = form_data.get('user_id')

            print("Received form data:", form_data)

            if not user_id:
                return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Form data received successfully", "data": form_data}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetAlternativasDeportivasView(APIView):
    """
    Endpoint para mostrar info general del beneficio de Alternativas Deportivas y Artísticas
    """

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            status_msg = request.data.get('status')

            if not user_id or not status_msg:
                return Response({
                    "error": "Parameters 'user_id' and 'status' are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)

            start_time = time.time()

            result = get_alternativas_deportivas(
                user_id=user_id,
                status=status_msg
            )

            end_time = time.time()
            result["execution_time"] = end_time - start_time

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"Error in GetAlternativasDeportivasView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetCatalogoActividadesView(APIView):
    """
    Endpoint para mostrar catálogo visual de todas las actividades deportivas y artísticas
    """

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            status_msg = request.data.get('status')

            if not user_id or not status_msg:
                return Response({
                    "error": "Parameters 'user_id' and 'status' are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)

            start_time = time.time()

            result = get_catalogo_actividades(
                user_id=user_id,
                status=status_msg
            )

            end_time = time.time()
            result["execution_time"] = end_time - start_time

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"Error in GetCatalogoActividadesView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetFlexibilidadInfoView(APIView):
    """
    Endpoint para mostrar info completa de medidas de Flexibilidad Laboral
    """

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            status_msg = request.data.get('status')

            if not user_id or not status_msg:
                return Response({
                    "error": "Parameters 'user_id' and 'status' are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)

            start_time = time.time()

            result = get_flexibilidad_info(
                user_id=user_id,
                status=status_msg
            )

            end_time = time.time()
            result["execution_time"] = end_time - start_time

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"Error in GetFlexibilidadInfoView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "healthy",
        "service": "biela",
        "message": "Bienestar Organizacional service is working properly"
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_available_functions(request):
    functions = [
        {
            "name": "get_alternativas_deportivas",
            "description": "Info general del beneficio de Alternativas Deportivas y Artísticas",
            "endpoint": "/api/v1/mental/alternativas/",
            "method": "POST",
            "required_params": ["user_id", "status"]
        },
        {
            "name": "get_catalogo_actividades",
            "description": "Catálogo visual completo de todas las actividades con imágenes, horarios e inscripción",
            "endpoint": "/api/v1/mental/catalogo/",
            "method": "POST",
            "required_params": ["user_id", "status"]
        },
        {
            "name": "get_flexibilidad_info",
            "description": "Info completa de Flexibilidad Laboral (Flexiacademia, Flexiespacio, Flexitiempo)",
            "endpoint": "/api/v1/mental/flexibilidad/",
            "method": "POST",
            "required_params": ["user_id", "status"]
        },
    ]

    return Response({
        "available_functions": functions,
        "total_functions": len(functions)
    }, status=status.HTTP_200_OK)
