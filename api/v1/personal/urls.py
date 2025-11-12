from django.urls import path, include

urlpatterns = [
    # Function endpoints
    path('functions/', include('apps.personal.urls')),
]
