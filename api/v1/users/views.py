from apps.users.services import UserService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.openapi import OpenApiResponse

class UserList(APIView):
    def __init__(self):
        self.user_service = UserService()

    @extend_schema(
        summary="Create new user",
        description="Creates a new user with the provided information",
        request=UserSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description="User created successfully",
                examples=[
                    OpenApiExample(
                        "Successful Response",
                        value={
                            "status": "User created successfully",
                            "user": {
                                "id": 1,
                                "name": "John",
                                "family_name": "Doe",
                                "email": "john@example.com",
                                "photo_url": "https://example.com/photo.jpg",
                                "created_at": "2024-01-30T12:00:00Z",
                                "updated_at": "2024-01-30T12:00:00Z"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad request",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "email": ["Enter a valid email address."],
                            "name": ["This field is required."]
                        }
                    ),
                    OpenApiExample(
                        "Service Error",
                        value={
                            "status": "User with this email already exists"
                        }
                    )
                ]
            )
        },
        tags=["Users"]
    )
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


    @extend_schema(
        summary="Get user by ID or email",
        description="Returns the user with the provided ID or email",
        parameters=[
            OpenApiParameter(
                name="user_id",
                description="The ID of the user",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name="email",
                description="The email of the user",
                required=False,
                type=OpenApiTypes.EMAIL,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="User found",
                examples=[
                    OpenApiExample(
                        "Successful Response",
                        value={
                            "id": 1,
                            "name": "John",
                            "family_name": "Doe",
                            "email": "john@example.com",
                            "photo_url": "https://example.com/photo.jpg",
                            "created_at": "2024-01-30T12:00:00Z",
                            "updated_at": "2024-01-30T12:00:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad request",
                examples=[
                    OpenApiExample(
                        "Missing Parameters",
                        value={"status": "User ID or email must be provided"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="User not found",
                examples=[
                    OpenApiExample(
                        "Not Found",
                        value={"status": "Not Found"}
                    )
                ]
            )
        },
        tags=["Users"]
    )
    @method_decorator(cache_page(60*15, key_prefix="user"))
    def get(self, request):
        user_id = request.query_params.get('user_id')
        email = request.query_params.get('email')
        
        if user_id is None and email is None:
            return Response(
                {"status": "User ID or email must be provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if email is not None:
            user = self.user_service.get_user_by_email(email)
            print(f"Fetching user by email: {email}")
        else:
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