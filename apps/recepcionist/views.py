from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .functions import (
    search_university_staff,
    answer_question_of_uni_premises,
    query_recepcionist_rag,
    get_location_events,
    get_restaurants,
    get_location_places,
    send_email
)


@api_view(['POST'])
def search_contacts(request):
    """Search university contacts by name"""
    try:
        name = request.data.get('name')
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Searching contacts...')

        if not name:
            return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = search_university_staff(name, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_premises_info(request):
    """Get information about university premises"""
    try:
        place = request.data.get('place')
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Getting premises information...')

        if not place:
            return Response({'error': 'place is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = answer_question_of_uni_premises(place, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_menus(request):
    """Search restaurant menus and dining information"""
    try:
        question = request.data.get('question')
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Searching menu information...')
        k = request.data.get('k', 3)
        restaurant_menus = request.data.get('restaurant_menus', None)

        if not question:
            return Response({'error': 'question is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = query_recepcionist_rag(user_id, question, k, status_msg, restaurant_menus)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def find_events(request):
    """Find events in a specific location"""
    try:
        location = request.data.get('location', 'Barranquilla')
        event_query = request.data.get('event_query', 'concerts')
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Searching for events...')

        result = get_location_events(location, user_id, status_msg, event_query)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def find_restaurants(request):
    """Find restaurants in a specific location"""
    try:
        location = request.data.get('location', 'Barranquilla')
        food_query = request.data.get('food_query', 'restaurants')
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Searching for restaurants...')

        result = get_restaurants(location, food_query, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def discover_places(request):
    """Discover places to visit in a location"""
    try:
        location = request.data.get('location', 'Barranquilla')
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Searching for places to visit...')
        location_query = request.data.get('location_query', '')

        result = get_location_places(location, user_id, status_msg, location_query)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_info_email(request):
    """Send information via email"""
    try:
        to_email = request.data.get('to_email')
        subject = request.data.get('subject')
        body = request.data.get('body')
        user_id = request.data.get('user_id', 1)
        status_msg = request.data.get('status', 'Sending email...')

        if not all([to_email, subject, body]):
            return Response(
                {'error': 'to_email, subject, and body are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = send_email(to_email, subject, body, status_msg, user_id)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
