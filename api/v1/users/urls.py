from django.urls import path
from .views import UserDetail, UserList





urlpatterns = [
    path('', UserList.as_view(), name='user-create'),
    path('<int:user_id>/', UserDetail.as_view(), name='user-detail'),

]

