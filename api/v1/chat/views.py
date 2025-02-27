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
from .serializers import ChatSerializer, ChatMessagesSerializer
from dotenv import load_dotenv
import os
import time
load_dotenv()


class Chat(APIView):
    permission_classes = [IsAuthenticated]  
    def __init__(self):
        self.chat_service = ChatService()


    def post(self, request):
        try:
            serializer = ChatSerializer(data=request.data)
            if serializer.is_valid():
                user_id = serializer.validated_data['user_id']
                user_input = serializer.validated_data['user_input']
                role_id = serializer.validated_data['role_id']
                start_time = time.time()
                response = self.chat_service.generate_response(
                    username="John Doe",
                    user_input=user_input,
                    user_id=user_id,
                    role_id=role_id,
                )
                end_time = time.time()
                print("Tiempo de respuesta: ", end_time - start_time)
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class ChatMessages(APIView):
    permission_classes = [IsAuthenticated]
    def __init__(self):
        self.chat_service = ChatService()

    def post(self, request):
        try:
            serializer = ChatMessagesSerializer(data=request.data)
            if serializer.is_valid():
                user_id = serializer.validated_data['user_id']
                role_id = serializer.validated_data['role_id']
                self.chat_service.save_current_conversation(user_id, role_id)
                self.chat_service.delete_current_conversation(user_id, role_id)
                return Response({"message": "Conversación guardada"}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        
    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            role_id = request.query_params.get('role_id')
            if not user_id or not role_id:
                return Response({"error": "user_id and role_id are required"}, status=status.HTTP_400_BAD_REQUEST)
            messages = self.chat_service.get_conversation(user_id, role_id)
            return Response(messages, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)