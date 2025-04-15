from apps.chat.services import ChatService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import ChatSerializer, ChatMessagesSerializer
from dotenv import load_dotenv
import time
load_dotenv()


class Chat(APIView):
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
                    user_input=user_input,
                    user_id=user_id,
                    role_id=role_id,
                )
                end_time = time.time()
                print("Tiempo de respuesta: ", end_time - start_time)
                response["time"] = end_time - start_time
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class ChatMessages(APIView):
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
                return Response({"message": "Conversation saved"}, status=status.HTTP_200_OK)
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
        
@api_view(["POST"])
def make_resume(request):
    try:
        serializer = ChatMessagesSerializer(data=request.data)
        if serializer.is_valid():
            chat = ChatService()
            user_id = serializer.validated_data['user_id']
            role_id = serializer.validated_data['role_id']
            chat.save_and_update_current_conversation(user_id, role_id)
            return Response({"message": "Conversación guardada"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(["POST"])
def upload_current_image(request):
    try:
        user_id = request.data.get('user_id')
        image = request.FILES.get('image')
        
        if not user_id or not image:
            return Response({"error": "user_id y image son requeridos"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not image.content_type.startswith('image/'):
            return Response({"error": "El archivo debe ser una imagen"}, status=status.HTTP_400_BAD_REQUEST)

        chat = ChatService()
        result = chat.upload_image(user_id, image)
        
        return Response({"message": "Imagen subida"}, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)