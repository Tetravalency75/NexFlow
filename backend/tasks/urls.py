from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/authority/', views.authority_dashboard_view, name='authority_dashboard'),
    path('dashboard/lead/', views.lead_dashboard_view, name='lead_dashboard'),
    path('dashboard/member/', views.member_dashboard_view, name='member_dashboard'),
    path('dashboard/learner/', views.learner_dashboard_view, name='learner_dashboard'),
    path('tasks/', views.tasks_view, name='tasks'),
    path('tasks/create/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_id>/update-status/', views.task_update_status_view, name='task_update_status'),
    path('tasks/<int:task_id>/delete/', views.task_delete_view, name='task_delete'),
    path('proofs/submit/', views.proof_submit_view, name='proof_submit'),
    path('proofs/<int:proof_id>/verify/', views.proof_verify_view, name='proof_verify'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('reports/', views.reports_view, name='reports'),
]
