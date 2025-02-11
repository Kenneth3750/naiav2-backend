from django.contrib import admin
from django.urls import path
from .views import UserDetail, UserList
from rest_framework.urlpatterns import format_suffix_patterns




urlpatterns = [
    path('', UserList.as_view(), name='user-create'),
    path('<int:user_id>/', UserDetail.as_view(), name='user-detail'),

]

