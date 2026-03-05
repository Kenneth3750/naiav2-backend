from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from apps.mental.functions import get_alternativas_deportivas, get_flexibilidad_info, get_catalogo_actividades, get_virtual_campus_tour, send_email, search_contacts_by_name, create_calendar_event, read_calendar_events, read_user_emails
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


class GetVirtualCampusTourView(APIView):
    """
    Endpoint para generar tour virtual interactivo del campus de Uninorte
    """

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            status_msg = request.data.get('status')
            language = request.data.get('language', 'Spanish')
            area_filter = request.data.get('area_filter')
            place_name = request.data.get('place_name')

            if not user_id or not status_msg:
                return Response({
                    "error": "Parameters 'user_id' and 'status' are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(user_id, int):
                return Response({
                    "error": "'user_id' must be an integer"
                }, status=status.HTTP_400_BAD_REQUEST)

            start_time = time.time()

            result = get_virtual_campus_tour(
                area_filter=area_filter,
                place_name=place_name,
                language=language,
                user_id=user_id,
                status=status_msg
            )

            end_time = time.time()
            result["execution_time"] = end_time - start_time

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"Error in GetVirtualCampusTourView: {str(e)}")
            return Response({
                "error": "Internal server error",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_email_view(request):
    """Enviar correo desde la cuenta de NAIA"""
    try:
        to_email = request.data.get('to_email')
        subject = request.data.get('subject')
        body = request.data.get('body')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([to_email, subject, body, user_id, status_msg]):
            return Response(
                {'error': 'to_email, subject, body, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = send_email(to_email, subject, body, status_msg, user_id)
        return Response(result)
    except Exception as e:
        logging.error(f"Error in send_email_view: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_contacts_view(request):
    """Buscar contactos por nombre"""
    try:
        name = request.data.get('name')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([name, user_id, status_msg]):
            return Response(
                {'error': 'name, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = search_contacts_by_name(name, user_id, status_msg)
        return Response(result)
    except Exception as e:
        logging.error(f"Error in search_contacts_view: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_event_view(request):
    """Crear evento en el calendario"""
    try:
        title = request.data.get('title')
        start_datetime = request.data.get('start_datetime')
        end_datetime = request.data.get('end_datetime')
        user_id = request.data.get('user_id')
        description = request.data.get('description', '')
        status_msg = request.data.get('status', 'Creando recordatorio...')

        if not all([title, start_datetime, end_datetime, user_id]):
            return Response(
                {'error': 'title, start_datetime, end_datetime, and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = create_calendar_event(title, start_datetime, end_datetime, user_id, description, status_msg)
        return Response(result)
    except Exception as e:
        logging.error(f"Error in create_event_view: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def read_calendar_view(request):
    """Leer eventos del calendario"""
    try:
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([start_date, end_date, user_id, status_msg]):
            return Response(
                {'error': 'start_date, end_date, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = read_calendar_events(start_date, end_date, user_id, status_msg)
        return Response(result)
    except Exception as e:
        logging.error(f"Error in read_calendar_view: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def read_emails_view(request):
    """Leer correos del usuario"""
    try:
        user_id = request.data.get('user_id')
        max_emails = request.data.get('max_emails', 10)
        unread_only = request.data.get('unread_only', False)
        search_query = request.data.get('search_query', None)
        read_full_content = request.data.get('read_full_content', False)
        specific_subject = request.data.get('specific_subject', None)
        status_msg = request.data.get('status', 'Consultando correos...')

        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = read_user_emails(user_id, max_emails, unread_only, search_query, read_full_content, specific_subject, status_msg)
        return Response(result)
    except Exception as e:
        logging.error(f"Error in read_emails_view: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        {
            "name": "get_virtual_campus_tour",
            "description": "Tour virtual interactivo del campus de Uninorte con imágenes e info detallada",
            "endpoint": "/api/v1/mental/tour/",
            "method": "POST",
            "required_params": ["user_id", "status", "language"],
            "optional_params": ["area_filter", "place_name"]
        },
        {
            "name": "send_email",
            "description": "Enviar correo desde la cuenta de NAIA Uninorte",
            "endpoint": "/api/v1/mental/send-email/",
            "method": "POST",
            "required_params": ["to_email", "subject", "body", "user_id", "status"]
        },
        {
            "name": "search_contacts_by_name",
            "description": "Buscar contactos en el directorio de Microsoft Graph",
            "endpoint": "/api/v1/mental/search-contacts/",
            "method": "POST",
            "required_params": ["name", "user_id", "status"]
        },
        {
            "name": "create_calendar_event",
            "description": "Crear evento o recordatorio en el calendario de Microsoft",
            "endpoint": "/api/v1/mental/create-event/",
            "method": "POST",
            "required_params": ["title", "start_datetime", "end_datetime", "user_id", "status"],
            "optional_params": ["description"]
        },
        {
            "name": "read_calendar_events",
            "description": "Leer eventos del calendario para un rango de fechas",
            "endpoint": "/api/v1/mental/read-calendar/",
            "method": "POST",
            "required_params": ["start_date", "end_date", "user_id", "status"]
        },
        {
            "name": "read_user_emails",
            "description": "Leer correos del usuario desde Microsoft Outlook",
            "endpoint": "/api/v1/mental/read-emails/",
            "method": "POST",
            "required_params": ["user_id", "status"],
            "optional_params": ["max_emails", "unread_only", "search_query", "read_full_content", "specific_subject"]
        },
    ]

    return Response({
        "available_functions": functions,
        "total_functions": len(functions)
    }, status=status.HTTP_200_OK)
