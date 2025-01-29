from apps.users.services import UserService
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class UserList(APIView):
    def __init__(self):
        self.user_service = UserService()

    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user = self.user_service.create_user(
                    serializer.validated_data["name"],
                    serializer.validated_data["family_name"],
                    serializer.validated_data["email"],
                    serializer.validated_data["photo_url"]
                )
                return Response(
                    {
                        "status": "User created successfully",
                        "user": {
                            "id": user.id,
                            "name": user.name,
                            "family_name": user.family_name,
                            "email": user.email,
                            "photo_url": user.photo_url,
                            "created_at": user.created_at,
                            "updated_at": user.updated_at
                        }
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"status": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserDetail(APIView):
    def __init__(self):
        self.user_service = UserService()

    @method_decorator(cache_page(60*15))
    def get(self, request, user_id):
        user = self.user_service.get_user_by_id(user_id)
        if user is None:
            return Response(
                {"status": "Not Found"},
                status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "id": user.id,
                "name": user.name,
                "family_name": user.family_name,
                "email": user.email,
                "photo_url": user.photo_url,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            },
            status=status.HTTP_200_OK
        )