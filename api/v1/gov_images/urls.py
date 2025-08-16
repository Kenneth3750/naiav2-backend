from django.urls import path
from .views import GovImages

urlpatterns = [
    path('', GovImages.as_view(), name='gov_images_list'),
    path('<str:filename>/', GovImages.as_view(), name='gov_images_detail'),
]