from apps.chat.services import ChatService
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.openapi import OpenApiResponse
from .serializers import ChatSerializer
from dotenv import load_dotenv
import os
load_dotenv()


class Chat(APIView):
    permission_classes = [IsAuthenticated]  
    def __init__(self):
        self.chat_service = ChatService()
        self.image_url = os.getenv("bucket_url")


    def post(self, request):
        try:
            serializer = ChatSerializer(data=request.data)
            if serializer.is_valid():
                user_id = serializer.validated_data['user_id']
                user_input = serializer.validated_data['user_input']
                thread_id = serializer.validated_data['thread_id']
                assistant_id = serializer.validated_data['assistant_id']

                response = self.chat_service.generate_response(
                    messages=None,
                    username="John Doe",
                    user_input=user_input,
                    image_url=f"{self.image_url}/current/user_{user_id}.jpg",
                    thread_id=thread_id,
                    assistant_id=assistant_id
                )
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)