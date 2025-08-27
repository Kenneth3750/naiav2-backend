from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from apps.gobernacion.functions import (
    frequently_asked_questions,
    search_traffic_fines,
    explain_passport_process,
    get_location_events,
    get_location_places
)
import time
import logging


class FrequentlyAskedQuestionsView(APIView):
    """
    Endpoint to query frequently asked questions from the Atlantic Department Government
    """
    
    def post(self, request):
        try:
            # Validate required parameters
            user_id = request.data.get('user_id')
            question = request.data.get('question')
            status_msg = request.data.get('status')
            
            if not user_id or not question or not status_msg:
                return Response({
                    "error": "Parameters 'user_id', 'question' and 'status' are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate types
            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            start_time = time.time()
            
            # Execute function
            result = frequently_asked_questions(
                user_id=user_id,
                question=question,
                status=status_msg
            )
            
            end_time = time.time()
            result["execution_time"] = end_time - start_time
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logging.error(f"Error in FrequentlyAskedQuestionsView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchTrafficFinesView(APIView):
    """
    Endpoint to search traffic fines in SIMIT system
    """
    
    def post(self, request):
        try:
            # Validate required parameters
            documento_placa = request.data.get('documento_placa')
            user_id = request.data.get('user_id')
            status_msg = request.data.get('status')
            
            if not documento_placa or not user_id or not status_msg:
                return Response({
                    "error": "Parameters 'documento_placa', 'user_id' and 'status' are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate types
            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            start_time = time.time()
            
            # Execute function
            result = search_traffic_fines(
                documento_placa=str(documento_placa),
                user_id=user_id,
                status=status_msg
            )
            
            end_time = time.time()
            result["execution_time"] = end_time - start_time
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logging.error(f"Error in SearchTrafficFinesView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExplainPassportProcessView(APIView):
    """
    Endpoint to explain the complete passport application process
    """
    
    def post(self, request):
        try:
            # Validate required parameters
            user_id = request.data.get('user_id')
            status_msg = request.data.get('status')
            
            if not user_id or not status_msg:
                return Response({
                    "error": "Parameters 'user_id' and 'status' are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate types
            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Optional parameters
            auto_slide_interval = request.data.get('auto_slide_interval', 4000)
            
            start_time = time.time()
            
            # Execute function
            result = explain_passport_process(
                user_id=user_id,
                status=status_msg,
                auto_slide_interval=auto_slide_interval
            )
            
            end_time = time.time()
            result["execution_time"] = end_time - start_time
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logging.error(f"Error in ExplainPassportProcessView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetLocationEventsView(APIView):
    """
    Endpoint to get events in Atlantic Department locations
    """
    
    def post(self, request):
        try:
            # Validate required parameters
            user_id = request.data.get('user_id')
            status_msg = request.data.get('status')
            event_query = request.data.get('event_query')
            location = request.data.get('location')
            
            if not user_id or not status_msg or not event_query or not location:
                return Response({
                    "error": "Parameters 'user_id', 'status', 'event_query' and 'location' are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate types
            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            start_time = time.time()
            
            # Execute function
            result = get_location_events(
                location=location,
                user_id=user_id,
                status=status_msg,
                event_query=event_query
            )
            
            end_time = time.time()
            result["execution_time"] = end_time - start_time
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logging.error(f"Error in GetLocationEventsView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetLocationPlacesView(APIView):
    """
    Endpoint to get tourist places in the Atlantic Department
    """
    
    def post(self, request):
        try:
            # Validate required parameters
            user_id = request.data.get('user_id')
            status_msg = request.data.get('status')
            location_query = request.data.get('location_query')
            location = request.data.get('location')
            
            if not user_id or not status_msg or not location_query or not location:
                return Response({
                    "error": "Parameters 'user_id', 'status', 'location_query' and 'location' are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate types
            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            start_time = time.time()
            
            # Execute function
            result = get_location_places(
                location=location,
                user_id=user_id,
                status=status_msg,
                location_query=location_query
            )
            
            end_time = time.time()
            result["execution_time"] = end_time - start_time
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logging.error(f"Error in GetLocationPlacesView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Additional endpoints using decorators for simpler functions
@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify the Atlantic Department Government service status
    """
    return Response({
        "status": "healthy",
        "service": "gobernacion",
        "message": "Atlantic Department Government service is working properly"
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_available_functions(request):
    """
    Endpoint to get the list of available functions
    """
    functions = [
        {
            "name": "frequently_asked_questions",
            "description": "Query frequently asked questions from the Atlantic Department Government",
            "endpoint": "/api/v1/gobernacion/faq/",
            "method": "POST",
            "required_params": ["user_id", "question", "status"]
        },
        {
            "name": "search_traffic_fines",
            "description": "Search traffic fines in SIMIT system",
            "endpoint": "/api/v1/gobernacion/traffic-fines/",
            "method": "POST",
            "required_params": ["documento_placa", "user_id", "status"]
        },
        {
            "name": "explain_passport_process",
            "description": "Explain complete passport application process",
            "endpoint": "/api/v1/gobernacion/passport-process/",
            "method": "POST",
            "required_params": ["user_id", "status"],
            "optional_params": ["auto_slide_interval"]
        },
        {
            "name": "get_location_events",
            "description": "Get events in Atlantic Department locations",
            "endpoint": "/api/v1/gobernacion/events/",
            "method": "POST",
            "required_params": ["user_id", "status", "event_query", "location"]
        },
        {
            "name": "get_location_places",
            "description": "Get tourist places in the Atlantic Department",
            "endpoint": "/api/v1/gobernacion/places/",
            "method": "POST",
            "required_params": ["user_id", "status", "location_query", "location"]
        }
    ]
    
    return Response({
        "available_functions": functions,
        "total_functions": len(functions)
    }, status=status.HTTP_200_OK)