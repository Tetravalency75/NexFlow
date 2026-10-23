from django.contrib import admin
from .models import Meeting, AttendanceResponse, HostNotification, ActionItem, MeetingMinutes

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'end_time', 'mode', 'status', 'host', 'created_at')
    list_filter = ('mode', 'status', 'date', 'host')
    search_fields = ('title', 'agenda', 'description', 'host__username', 'location')

@admin.register(MeetingMinutes)
class MeetingMinutesAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('meeting__title', 'created_by__username', 'discussion_summary', 'decisions_made')

@admin.register(AttendanceResponse)
class AttendanceResponseAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'attendee', 'status', 'joined_via_link', 'confirmed_attended', 'submitted_at')
    list_filter = ('status', 'joined_via_link', 'confirmed_attended', 'submitted_at')
    search_fields = ('meeting__title', 'attendee__username', 'absence_reason')

@admin.register(HostNotification)
class HostNotificationAdmin(admin.ModelAdmin):
    list_display = ('host', 'meeting', 'attendee', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('meeting__title', 'attendee__username', 'reason')

@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'meeting', 'owner', 'status', 'due_date', 'is_converted', 'created_at')
    list_filter = ('status', 'is_converted', 'due_date')
    search_fields = ('title', 'description', 'owner__username', 'meeting__title')

