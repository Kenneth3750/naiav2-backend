from django.contrib import admin
from django.urls import path
from .views import UserDetail

urlpatterns = [
    path('<int:user_id>/', UserDetail.as_view())
]
