from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
import os

class TaskStatus(models.TextChoices):
    TODO = 'TODO', 'To Do'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    DONE = 'DONE', 'Done'

class TaskPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'

class RaciRole(models.TextChoices):
    RESPONSIBLE = 'R', 'Responsible (R)'
    ACCOUNTABLE = 'A', 'Accountable (A)'
    CONSULTED = 'C', 'Consulted (C)'
    INFORMED = 'I', 'Informed (I)'

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
    )
    project = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Project or domain associated with this deliverable"
    )
    raci_role = models.CharField(
        max_length=5,
        choices=RaciRole.choices,
        default=RaciRole.RESPONSIBLE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return f"{self.title} [{self.status}] -> {self.assigned_to.display_name}"

    @property
    def is_overdue(self):
        if self.due_date and self.status != TaskStatus.DONE:
            return self.due_date < timezone.now().date()
        return False

def validate_proof_file(file):
    max_mb = 10
    if file.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Maximum upload file size is {max_mb}MB.")
    
    allowed_exts = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.txt', '.doc', '.docx']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_exts:
        raise ValidationError(f"Unsupported file format '{ext}'. Allowed: {', '.join(allowed_exts)}")

class ProofStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Verification'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class ProofOfWork(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='proof_submissions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='proof_submissions'
    )
    description = models.TextField(help_text="Detailed description of completed deliverable")
    proof_file = models.FileField(
        upload_to='proofs/%Y/%m/',
        blank=True,
        null=True,
        validators=[validate_proof_file],
        help_text="Optional document or screenshot artifact (Max 10MB)"
    )
    proof_url = models.URLField(
        blank=True,
        default='',
        help_text="Optional link to Git commit, PR, or hosted deliverable"
    )
    status = models.CharField(
        max_length=20,
        choices=ProofStatus.choices,
        default=ProofStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_proofs'
    )
    review_feedback = models.TextField(blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    points_awarded = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Proof by {self.user.display_name} for '{self.task.title}' [{self.status}]"

    def clean(self):
        super().clean()
        if not self.proof_file and not self.proof_url and not self.description:
            raise ValidationError("You must provide either a description, file artifact, or link as proof.")
        if self.reviewed_by and self.reviewed_by == self.user:
            raise ValidationError("Authorities cannot review or approve their own proof-of-work submissions.")
