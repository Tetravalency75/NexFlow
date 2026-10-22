from django.urls import path
from . import views

urlpatterns = [
    path('meetings/', views.meetings_view, name='meetings'),
    path('meetings/create/', views.meeting_create_view, name='meeting_create'),
    path('meetings/<int:meeting_id>/attendance/', views.attendance_submit_view, name='attendance_submit'),
    path('meetings/<int:meeting_id>/minutes/', views.meeting_minutes_view, name='meeting_minutes'),
    path('meetings/<int:meeting_id>/action-items/create/', views.action_item_create_view, name='action_item_create'),
    path('meetings/action-items/<int:item_id>/convert/', views.action_item_convert_view, name='action_item_convert'),
]
