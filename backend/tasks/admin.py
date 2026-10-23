from django.contrib import admin
from .models import Task, ProofOfWork

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'raci_role', 'assigned_to', 'created_by', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'raci_role', 'due_date')
    search_fields = ('title', 'description', 'assigned_to__username', 'assigned_to__email')

@admin.register(ProofOfWork)
class ProofOfWorkAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'status', 'reviewed_by', 'points_awarded', 'created_at', 'reviewed_at')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('task__title', 'user__username', 'description', 'review_feedback')
