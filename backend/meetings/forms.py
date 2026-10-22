from django import forms
from django.contrib.auth import get_user_model
from .models import Meeting, AttendanceResponse, ActionItem, AttendanceStatus

User = get_user_model()

class MeetingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'required': True})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input', 'type': 'time', 'required': True})
    )
    attendees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
        required=False
    )

    class Meta:
        model = Meeting
        fields = ['title', 'agenda', 'date', 'start_time', 'meeting_link', 'attendees']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Sprint Review & RACI Alignment', 'required': True}),
            'agenda': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Key discussion points, topics, goals...'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://meet.google.com/xyz-abcd-efg'}),
        }

class AttendanceResponseForm(forms.ModelForm):
    class Meta:
        model = AttendanceResponse
        fields = ['status', 'absence_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'absence_reason': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Please specify why you are unable to attend...'}),
        }

class ActionItemForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )

    class Meta:
        model = ActionItem
        fields = ['description', 'owner', 'due_date']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Specific follow-up action...', 'required': True}),
        }
