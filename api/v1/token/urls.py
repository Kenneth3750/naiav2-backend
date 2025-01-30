from django.urls import path, include
from .views import RegisterAndLoginView, LogoutView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', RegisterAndLoginView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
]