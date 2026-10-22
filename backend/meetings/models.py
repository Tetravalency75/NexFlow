from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from tasks.models import Task

def validate_meeting_url(value):
    if value:
        val = value.strip().lower()
        if not (val.startswith('https://') or val.startswith('http://')):
            raise ValidationError("Meeting URL must use an allowed protocol, preferably https:// (e.g. Google Meet or Teams).")

class Meeting(models.Model):
    title = models.CharField(max_length=200)
    agenda = models.TextField(blank=True, default='')
    date = models.DateField()
    start_time = models.TimeField()
    meeting_link = models.URLField(
        blank=True,
        default='',
        validators=[validate_meeting_url],
        help_text="External video conference link (Google Meet, Microsoft Teams, Zoom)"
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_meetings'
    )
    attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='invited_meetings',
        blank=True
    )
    minutes = models.TextField(blank=True, default='', help_text="Official recorded minutes of the meeting")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.title} on {self.date} at {self.start_time} (Host: {self.host.display_name})"

    @property
    def is_upcoming(self):
        meeting_datetime = timezone.datetime.combine(self.date, self.start_time)
        return timezone.make_aware(meeting_datetime) >= timezone.now()

class AttendanceStatus(models.TextChoices):
    ATTENDING = 'ATTENDING', 'Attending'
    ABSENT = 'ABSENT', 'Unable to Attend'

class AttendanceResponse(models.Model):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='attendance_responses'
    )
    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_responses'
    )
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ATTENDING
    )
    absence_reason = models.TextField(
        blank=True,
        default='',
        help_text="Reason for being unable to attend"
    )
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('meeting', 'attendee')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.attendee.display_name} - {self.status} for '{self.meeting.title}'"

class HostNotification(models.Model):
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='host_notifications'
    )
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='host_notifications'
    )
    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    reason = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Absence Alert for {self.host.display_name}: {self.attendee.display_name} reported absent"

class ActionItem(models.Model):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='action_items'
    )
    description = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='action_items'
    )
    due_date = models.DateField(null=True, blank=True)
    is_converted = models.BooleanField(default=False, help_text="Flags whether a Task was generated")
    converted_task = models.OneToOneField(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='originating_action_item'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        status = "[Converted]" if self.is_converted else "[Open]"
        return f"{status} {self.description} -> {self.owner.display_name}"
