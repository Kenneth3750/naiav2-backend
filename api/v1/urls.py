from django.urls import path, include



urlpatterns = [
    path('users/', include('api.v1.users.urls')),
    path('token/', include('api.v1.token.urls')),
    path('api-auth/', include('rest_framework.urls')), 
]