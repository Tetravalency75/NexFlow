from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone
from tasks.models import Task

def validate_meeting_url(value):
    if value:
        val = value.strip()
        val_lower = val.lower()
        if not (val_lower.startswith('https://') or val_lower.startswith('http://')):
            raise ValidationError("Meeting URL must use an allowed protocol, preferably https:// (e.g. Google Meet or Teams).")
        validator = URLValidator(schemes=['http', 'https'])
        validator(val)

class MeetingMode(models.TextChoices):
    VIRTUAL = 'VIRTUAL', 'Virtual'
    IN_PERSON = 'IN_PERSON', 'In-Person'

class MeetingStatus(models.TextChoices):
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class Meeting(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='', help_text="Detailed meeting description and context")
    agenda = models.TextField(blank=True, default='', help_text="Discussion agenda and topics")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True, help_text="Scheduled end time")
    mode = models.CharField(
        max_length=20,
        choices=MeetingMode.choices,
        default=MeetingMode.VIRTUAL,
        help_text="Meeting mode: Virtual or In-Person"
    )
    meeting_link = models.URLField(
        blank=True,
        default='',
        validators=[validate_meeting_url],
        help_text="External video conference link (Google Meet, Microsoft Teams, Zoom)"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Physical location for in-person meetings"
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
    status = models.CharField(
        max_length=20,
        choices=MeetingStatus.choices,
        default=MeetingStatus.SCHEDULED,
        help_text="Status of the meeting"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.title} on {self.date} at {self.start_time} (Host: {self.host.display_name})"

    @property
    def created_by(self):
        return self.host

    @created_by.setter
    def created_by(self, user):
        self.host = user

    @property
    def is_upcoming(self):
        if self.status == MeetingStatus.CANCELLED:
            return False
        meeting_datetime = timezone.datetime.combine(self.date, self.start_time)
        return timezone.make_aware(meeting_datetime) >= timezone.now()

    @property
    def is_virtual(self):
        return self.mode == MeetingMode.VIRTUAL

    @property
    def is_in_person(self):
        return self.mode == MeetingMode.IN_PERSON

    def clean(self):
        super().clean()
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError({'end_time': "End time must be later than start time."})
        if self.mode == MeetingMode.VIRTUAL and self.meeting_link:
            validate_meeting_url(self.meeting_link)

class AttendanceStatus(models.TextChoices):
    ATTENDING = 'ATTENDING', 'Attending'
    ABSENT = 'ABSENT', 'Unable to Attend'
    CONFIRMED_ATTENDED = 'CONFIRMED_ATTENDED', 'Confirmed Attended'

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
    joined_via_link = models.BooleanField(
        default=False,
        help_text="Records that attendee opened or joined the virtual meeting link"
    )
    joined_at = models.DateTimeField(null=True, blank=True)
    confirmed_attended = models.BooleanField(
        default=False,
        help_text="Official attendance confirmed by meeting organizer or host"
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

class MeetingMinutes(models.Model):
    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name='official_minutes'
    )
    discussion_summary = models.TextField(
        blank=True,
        default='',
        help_text="Summary of discussion during the meeting"
    )
    decisions_made = models.TextField(
        blank=True,
        default='',
        help_text="Key decisions reached"
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text="General notes, observations, and follow-ups"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recorded_minutes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Meeting Minutes"
        verbose_name_plural = "Meeting Minutes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Minutes: {self.meeting.title} (by {self.created_by.display_name})"

class ActionItemStatus(models.TextChoices):
    TODO = 'TODO', 'To Do'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    DONE = 'DONE', 'Done'

class ActionItem(models.Model):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='action_items'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Action item title or short summary"
    )
    description = models.TextField(
        help_text="Detailed action item description"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='action_items',
        help_text="Assigned team member"
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ActionItemStatus.choices,
        default=ActionItemStatus.TODO
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_action_items'
    )
    is_converted = models.BooleanField(
        default=False,
        help_text="Flags whether a Task was generated"
    )
    converted_task = models.OneToOneField(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='originating_action_item'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        title_str = self.title or self.description[:50]
        return f"[{self.status}] {title_str} -> {self.owner.display_name}"

    @property
    def assigned_to(self):
        return self.owner

    @assigned_to.setter
    def assigned_to(self, user):
        self.owner = user

    def save(self, *args, **kwargs):
        if not self.title and self.description:
            self.title = self.description[:200]
        super().save(*args, **kwargs)

