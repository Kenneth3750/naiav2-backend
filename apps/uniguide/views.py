from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .functions import (
    query_university_rag,
    get_university_calendar_multi_month,
    get_virtual_campus_tour,
    search_internet_for_uni_answers,
    send_email,
    search_contacts_by_name,
    create_calendar_event
)


@api_view(['POST'])
def university_rag_query(request):
    """Query Universidad del Norte's RAG database"""
    try:
        question = request.data.get('question')
        user_id = request.data.get('user_id', 1)
        k = request.data.get('k', 3)
        status_msg = request.data.get('status', 'Searching university documents...')

        if not question:
            return Response({'error': 'question is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = query_university_rag(user_id, question, k, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_campus_calendar(request):
    """Get university calendar events for multiple months"""
    try:
        months = request.data.get('months', [])
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Fetching university calendar...')

        if not months:
            return Response({'error': 'months list is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = get_university_calendar_multi_month(user_id, months, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def virtual_campus_tour(request):
    """Generate virtual campus tour"""
    try:
        area_filter = request.data.get('area_filter', None)
        place_name = request.data.get('place_name', None)
        language = request.data.get('language', 'Spanish')
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Generating virtual tour...')

        result = get_virtual_campus_tour(area_filter, place_name, language, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_university_internet(request):
    """Search internet for Universidad del Norte information"""
    try:
        query = request.data.get('query')
        user_id = request.data.get('user_id')
        image_query = request.data.get('image_query', '')
        status_msg = request.data.get('status', 'Searching the internet...')

        if not query or user_id is None:
            return Response({'error': 'query and user_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        result = search_internet_for_uni_answers(query, status_msg, user_id, image_query)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_university_email(request):
    """Send email through university system"""
    try:
        to_email = request.data.get('to_email')
        subject = request.data.get('subject')
        body = request.data.get('body')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status', 'Sending email...')

        if not all([to_email, subject, body, user_id]):
            return Response(
                {'error': 'to_email, subject, body, and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = send_email(to_email, subject, body, status_msg, user_id)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_university_contacts(request):
    """Search university directory for contacts"""
    try:
        name = request.data.get('name')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status', 'Searching contacts...')

        if not name or user_id is None:
            return Response({'error': 'name and user_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        result = search_contacts_by_name(name, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_university_calendar_event(request):
    """Create calendar event for university activities"""
    try:
        title = request.data.get('title')
        start_datetime = request.data.get('start_datetime')
        end_datetime = request.data.get('end_datetime')
        user_id = request.data.get('user_id')
        description = request.data.get('description', '')
        status_msg = request.data.get('status', 'Creating calendar event...')

        if not all([title, start_datetime, end_datetime, user_id]):
            return Response(
                {'error': 'title, start_datetime, end_datetime, and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = create_calendar_event(title, start_datetime, end_datetime, user_id, description, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
