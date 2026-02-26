from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from apps.mompox.functions import about_mompox_inteligente, get_mompox_news
import time
import logging


class AboutMompoxInteligenteView(APIView):
    """
    Endpoint to explain what Mompox Inteligente is
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

            result = about_mompox_inteligente(
                user_id=user_id,
                status=status_msg
            )

            end_time = time.time()
            result["execution_time"] = end_time - start_time

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"Error in AboutMompoxInteligenteView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetMompoxNewsView(APIView):
    """
    Endpoint to get latest news from Mompox Inteligente
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

            limit = request.data.get('limit', 6)

            start_time = time.time()

            result = get_mompox_news(
                user_id=user_id,
                status=status_msg,
                limit=limit
            )

            end_time = time.time()
            result["execution_time"] = end_time - start_time

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"Error in GetMompoxNewsView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify the Mompox service status
    """
    return Response({
        "status": "healthy",
        "service": "mompox",
        "message": "Mompox - Gobernación de Bolívar service is working properly"
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_available_functions(request):
    """
    Endpoint to get the list of available functions
    """
    functions = [
        {
            "name": "about_mompox_inteligente",
            "description": "Explain what Mompox Inteligente is with video and visual content",
            "endpoint": "/api/v1/mompox/about/",
            "method": "POST",
            "required_params": ["user_id", "status"]
        },
        {
            "name": "get_mompox_news",
            "description": "Get latest news from Mompox Inteligente",
            "endpoint": "/api/v1/mompox/news/",
            "method": "POST",
            "required_params": ["user_id", "status"],
            "optional_params": ["limit"]
        },
    ]

    return Response({
        "available_functions": functions,
        "total_functions": len(functions)
    }, status=status.HTTP_200_OK)
