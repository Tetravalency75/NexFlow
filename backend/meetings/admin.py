from django.contrib import admin
from .models import Meeting, AttendanceResponse, HostNotification, ActionItem

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'host', 'created_at')
    list_filter = ('date', 'host')
    search_fields = ('title', 'agenda', 'host__username')

@admin.register(AttendanceResponse)
class AttendanceResponseAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'attendee', 'status', 'submitted_at')
    list_filter = ('status', 'submitted_at')
    search_fields = ('meeting__title', 'attendee__username', 'absence_reason')

@admin.register(HostNotification)
class HostNotificationAdmin(admin.ModelAdmin):
    list_display = ('host', 'meeting', 'attendee', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('meeting__title', 'attendee__username', 'reason')

@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'meeting', 'owner', 'due_date', 'is_converted', 'created_at')
    list_filter = ('is_converted', 'due_date')
    search_fields = ('description', 'owner__username', 'meeting__title')
