from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView



urlpatterns = [
    path('users/', include('api.v1.users.urls')),
    path('token/', include('api.v1.token.urls')),
    path('chat/', include('api.v1.chat.urls')),
    path('researcher/', include('api.v1.researcher.urls')),
    path('api-auth/', include('rest_framework.urls')), 
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]