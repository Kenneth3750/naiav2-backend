from apps.users.services import UserService
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status



class UserDetail(APIView):
    def __init__(self):
        self.user_service = UserService()

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

