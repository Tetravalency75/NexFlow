from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'job_title', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('NEXFlow Role & Workspace Profile', {'fields': ('role', 'job_title', 'avatar', 'department', 'points')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('NEXFlow Role & Workspace Profile', {'fields': ('role', 'job_title', 'avatar', 'department')}),
    )
