from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Meeting, AttendanceResponse, ActionItem, MeetingMinutes, MeetingMode, validate_meeting_url

User = get_user_model()

class MeetingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'required': True})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input', 'type': 'time', 'required': True})
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'})
    )
    mode = forms.ChoiceField(
        choices=MeetingMode.choices,
        initial=MeetingMode.VIRTUAL,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    attendees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
        required=False
    )

    class Meta:
        model = Meeting
        fields = [
            'title', 'description', 'agenda', 'date', 'start_time', 'end_time',
            'mode', 'meeting_link', 'location', 'attendees'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Sprint Review & RACI Alignment', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'High-level context and meeting objective...'}),
            'agenda': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Key discussion points, topics, deliverables...'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://meet.google.com/xyz-abcd-efg'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Meeting Room 302 or Campus Hub'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        mode = cleaned_data.get('mode')
        meeting_link = cleaned_data.get('meeting_link')

        if not mode:
            cleaned_data['mode'] = MeetingMode.VIRTUAL
            mode = MeetingMode.VIRTUAL

        if start_time and end_time:
            if end_time <= start_time:
                self.add_error('end_time', "End time must be later than start time.")

        if mode == MeetingMode.VIRTUAL and meeting_link:
            try:
                validate_meeting_url(meeting_link)
            except ValidationError as err:
                self.add_error('meeting_link', err)

        return cleaned_data

class MeetingMinutesForm(forms.ModelForm):
    class Meta:
        model = MeetingMinutes
        fields = ['discussion_summary', 'decisions_made', 'notes']
        widgets = {
            'discussion_summary': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Summarize key discussion points, review items...'}),
            'decisions_made': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Document concrete decisions and consensus reached...'}),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Observations, follow-up timelines, general notes...'}),
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
        fields = ['title', 'description', 'owner', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Short title (optional)'}),
            'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Specific follow-up action...', 'required': True}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

