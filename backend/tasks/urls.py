from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('tasks/', views.tasks_view, name='tasks'),
    path('tasks/create/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_id>/update-status/', views.task_update_status_view, name='task_update_status'),
    path('proofs/submit/', views.proof_submit_view, name='proof_submit'),
    path('proofs/<int:proof_id>/verify/', views.proof_verify_view, name='proof_verify'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('reports/', views.reports_view, name='reports'),
]
