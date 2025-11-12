from django.urls import path
from . import views

urlpatterns = [
    path('interview/', views.job_interview_simulation, name='job_interview_simulation'),
    path('appearance/', views.professional_appearance_analysis, name='professional_appearance_analysis'),
    path('report/', views.training_report_generation, name='training_report_generation'),
    path('reports/', views.list_training_reports, name='list_training_reports'),
    path('report/<int:report_id>/', views.get_training_report, name='get_training_report'),
    path('cv/', views.build_cv, name='build_cv'),
]
