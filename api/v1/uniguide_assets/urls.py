from django.urls import path
from .views import UniguideAssets

urlpatterns = [
    path('', UniguideAssets.as_view(), name='uniguide_assets_list'),
    path('<str:filename>/', UniguideAssets.as_view(), name='uniguide_assets_detail'),
]
