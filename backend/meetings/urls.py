from django.urls import path
from . import views

urlpatterns = [
    path('meetings/', views.meetings_view, name='meetings'),
    path('meetings/upcoming/', views.meetings_upcoming_view, name='meetings_upcoming'),
    path('meetings/past/', views.meetings_past_view, name='meetings_past'),
    path('meetings/<int:meeting_id>/', views.meeting_detail_view, name='meeting_detail'),
    path('meetings/create/', views.meeting_create_view, name='meeting_create'),
    path('meetings/<int:meeting_id>/edit/', views.meeting_edit_view, name='meeting_edit'),
    path('meetings/<int:meeting_id>/cancel/', views.meeting_cancel_view, name='meeting_cancel'),
    path('meetings/<int:meeting_id>/join/', views.meeting_join_view, name='meeting_join'),
    path('meetings/<int:meeting_id>/minutes/', views.meeting_minutes_view, name='meeting_minutes'),
    path('meetings/<int:meeting_id>/action-items/', views.meeting_action_items_view, name='meeting_action_items'),
    path('meetings/<int:meeting_id>/action-items/create/', views.action_item_create_view, name='action_item_create'),
    path('meetings/action-items/<int:item_id>/status/', views.action_item_status_view, name='action_item_status'),
    path('meetings/action-items/<int:item_id>/convert/', views.action_item_convert_view, name='action_item_convert'),
    path('meetings/<int:meeting_id>/attendance/', views.attendance_submit_view, name='attendance_submit'),
]

