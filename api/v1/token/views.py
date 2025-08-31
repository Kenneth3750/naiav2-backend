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
    def get(self, request):
        """
        Genera un token ephímero para OpenAI Realtime API
        """
        try:
            # Obtener la API key de OpenAI desde las variables de entorno
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
                    "audio": {
                        "output": {
                            "voice": "marin",
                        },
                    },
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

            # Verificar si la respuesta fue exitosa
            if response.status_code == 200:
                data = response.json()
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {
                        "error": "Failed to generate token",
                        "details": response.text
                    },
                    status=response.status_code
                )

        except requests.exceptions.Timeout:
            return Response(
                {"error": "Request timeout - OpenAI API took too long to respond"},
                status=status.HTTP_408_REQUEST_TIMEOUT
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Network error: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            return Response(
                {"error": f"Token generation error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )