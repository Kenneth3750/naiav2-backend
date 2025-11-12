from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .functions import (
    get_current_news,
    get_weather,
    send_email_on_behalf_of_user,
    search_contacts_by_name,
    read_calendar_events,
    create_calendar_event,
    read_user_emails,
    explain_naia_roles
)


@api_view(['POST'])
def get_news(request):
    """Get latest news from a specific location"""
    try:
        location = request.data.get('location')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')
        query = request.data.get('query')
        language = request.data.get('language')

        if not all([location, user_id, status_msg, query, language]):
            return Response(
                {'error': 'location, user_id, status, query, and language are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = get_current_news(location, user_id, status_msg, query, language)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_weather_info(request):
    """Get weather information for a location"""
    try:
        location = request.data.get('location')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([location, user_id, status_msg]):
            return Response(
                {'error': 'location, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = get_weather(location, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_email(request):
    """Send email on behalf of user"""
    try:
        to_email_or_name = request.data.get('to_email_or_name')
        subject = request.data.get('subject')
        body = request.data.get('body')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([to_email_or_name, subject, body, user_id, status_msg]):
            return Response(
                {'error': 'to_email_or_name, subject, body, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = send_email_on_behalf_of_user(to_email_or_name, subject, body, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_contacts(request):
    """Search contacts by name"""
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
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def read_calendar(request):
    """Read calendar events for a date range"""
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
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_event(request):
    """Create calendar event"""
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


@api_view(['POST'])
def read_emails(request):
    """Read user emails"""
    try:
        user_id = request.data.get('user_id')
        max_emails = request.data.get('max_emails', 10)
        unread_only = request.data.get('unread_only', False)
        search_query = request.data.get('search_query', None)
        read_full_content = request.data.get('read_full_content', False)
        specific_subject = request.data.get('specific_subject', None)
        status_msg = request.data.get('status', 'Reading emails...')

        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = read_user_emails(user_id, max_emails, unread_only, search_query, read_full_content, specific_subject, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def explain_roles(request):
    """Explain NAIA roles"""
    try:
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')
        auto_slide_interval = request.data.get('auto_slide_interval', 3000)

        if not all([user_id, status_msg]):
            return Response({'error': 'user_id and status are required'}, status=status.HTTP_400_BAD_REQUEST)

        result = explain_naia_roles(auto_slide_interval, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
