from django import forms
from django.contrib.auth import get_user_model
from .models import Task, ProofOfWork, TaskPriority, RaciRole, ProofStatus

User = get_user_model()

class TaskForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'required': True}),
        empty_label="Select Team Member"
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'raci_role', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Task title...', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Task requirements and context...'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'raci_role': forms.Select(attrs={'class': 'form-select'}),
        }

class ProofSubmissionForm(forms.ModelForm):
    class Meta:
        model = ProofOfWork
        fields = ['task', 'description', 'proof_file', 'proof_url']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Describe what was delivered, milestones met, and testing performed...', 'required': True}),
            'proof_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://github.com/... or staging URL'}),
            'proof_file': forms.FileInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Users can only submit proof for tasks assigned to them or created by them (unless Authority)
            if user.is_authority:
                self.fields['task'].queryset = Task.objects.all()
            else:
                self.fields['task'].queryset = Task.objects.filter(assigned_to=user)

class ProofReviewForm(forms.Form):
    status = forms.ChoiceField(
        choices=[(ProofStatus.APPROVED, 'Approve Proof (+10 Points)'), (ProofStatus.REJECTED, 'Reject Proof')],
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    review_feedback = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Constructive review feedback for the submitter...'}),
        required=False
    )
