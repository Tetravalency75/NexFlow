from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    AUTHORITY = 'Authority', 'Authority'
    LEAD = 'Lead', 'Lead'
    MEMBER = 'Member', 'Member'
    LEARNER = 'Learner', 'Learner'

class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text="Workspace access level and responsibility tier"
    )
    job_title = models.CharField(max_length=120, blank=True, default='')
    avatar = models.CharField(max_length=255, default='images/avatar-1.svg')
    department = models.CharField(max_length=100, blank=True, default='Engineering')
    points = models.IntegerField(default=0, help_text="Total verified leaderboard points")

    class Meta:
        ordering = ['username']

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name if full_name else self.username} ({self.role})"

    @property
    def display_name(self):
        full_name = self.get_full_name()
        return full_name if full_name else self.username

    @property
    def is_authority(self):
        return self.role == Role.AUTHORITY or self.is_superuser

    @property
    def is_lead(self):
        return self.role == Role.LEAD

    @property
    def is_member(self):
        return self.role == Role.MEMBER

    @property
    def is_learner(self):
        return self.role == Role.LEARNER

    @property
    def can_assign_tasks(self):
        return self.role in [Role.AUTHORITY, Role.LEAD] or self.is_superuser

    @property
    def can_create_meetings(self):
        return self.role in [Role.AUTHORITY, Role.LEAD] or self.is_superuser

    @property
    def can_verify_proof(self):
        return self.role == Role.AUTHORITY or self.is_superuser

    def get_dashboard_url_name(self):
        if self.is_authority:
            return 'authority_dashboard'
        elif self.is_lead:
            return 'lead_dashboard'
        elif self.is_learner:
            return 'learner_dashboard'
        return 'member_dashboard'
