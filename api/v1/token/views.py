from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.users.models import User
import requests
from dotenv import load_dotenv
import json
import os
from datetime import datetime
from apps.roles.services import RealtimeRoleService
from apps.chat.services import RealtimeChatService
load_dotenv()

class RegisterAndLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email')
            user = User.objects.get(email=email)
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'No user found with this email'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Logout exitoso"}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class OpenAIRealtimeTokenView(APIView):
    def post(self, request):
        """
        Genera un token ephímero para OpenAI Realtime API
        """
        try:
            # Obtener la API key de OpenAI desde las variables de entorno
            role_id = request.data.get('roleId')
            user_id = request.data.get('user_id')
            print(f"Role ID: {role_id}, User ID: {user_id} para el token efímero")
            realtime_role_service = RealtimeRoleService(role_id)
            realtime_chat = RealtimeChatService(user_id, role_id)
            memory = realtime_chat.get_memory()
            tools, prompt = realtime_role_service.get_role(user_id, memory)
            api_key = os.getenv("open_ai")
            if not api_key:
                return Response(
                    {"error": "OpenAI API key not configured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Configuración de la sesión
            session_config = {
                "session": {
                    "type": "realtime",
                    "model": "gpt-realtime",
                    "output_modalities": ["audio"],
                    "audio": {
                        "output": {
                            "voice": "marin",
                        },
                    },
                    "instructions": prompt,
                    "tools": tools,
                    "tool_choice": "auto"
                }
            }

            # Hacer la petición a OpenAI
            response = requests.post(
                "https://api.openai.com/v1/realtime/client_secrets",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=session_config,
                timeout=30
            )



            if response.status_code == 200:
                data = response.json()
                expires_at_timestamp = data.get("expires_at")
                if expires_at_timestamp:
                    expires_at_datetime = datetime.utcfromtimestamp(expires_at_timestamp)
                    expires_at_formatted = expires_at_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    expires_at_formatted = None
                data = {
                    "client_secret": data.get("value"),
                    "expires_at": expires_at_formatted
                }
                return Response(data, status=status.HTTP_200_OK)

            else:
                print(f"Failed to generate token - {response.status_code}")
                print(f"Response details: {response.text}")
                return Response(
                    {
                        "error": "Failed to generate token",
                        "details": response.text
                    },
                    status=response.status_code
                )

        except requests.exceptions.Timeout:
            print("Request timeout - OpenAI API took too long to respond")
            return Response(
                {"error": "Request timeout - OpenAI API took too long to respond"},
                status=status.HTTP_408_REQUEST_TIMEOUT
            )
        except requests.exceptions.RequestException as e:
            print(f"Network error: {str(e)}")
            return Response(
                {"error": f"Network error: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            print(f"Token generation error: {str(e)}")
            return Response(
                {"error": f"Token generation error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )