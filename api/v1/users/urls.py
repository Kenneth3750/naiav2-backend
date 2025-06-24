from django.urls import path
from .views import UserDetail, UserList





urlpatterns = [
    path('', UserList.as_view(), name='user-create'),
    path('get/', UserDetail.as_view(), name='user-detail'),
]

