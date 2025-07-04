from django.urls import path
from .views import UserDetail, UserList, UserToken





urlpatterns = [
    path('', UserList.as_view(), name='user-create'),
    path('get/', UserDetail.as_view(), name='user-detail'),
    path('token/', UserToken.as_view(), name='user-token'),
]

