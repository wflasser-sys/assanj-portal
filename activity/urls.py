from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.activity_logs, name='activity_logs'),
    path('project/<int:pk>/', views.activity_logs_for_project, name='activity_logs_project'),
]
