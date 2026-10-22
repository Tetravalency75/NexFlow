from django import forms
from django.contrib.auth import authenticate
from .models import User, Role

class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Work Email or Username",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'name@nexflow.io or username',
            'id': 'login-email',
            'required': True,
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••••••',
            'id': 'login-password',
            'required': True,
        })
    )
    remember_me = forms.BooleanField(required=False, initial=True)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('username_or_email', '').strip()
        password = cleaned_data.get('password')

        if identifier and password:
            # Check if identifier is email or username
            user_obj = User.objects.filter(email__iexact=identifier).first()
            username = user_obj.username if user_obj else identifier

            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Invalid credentials. Please verify your email/username and password.")
            if not user.is_active:
                raise forms.ValidationError("This user account is inactive.")
            cleaned_data['user'] = user

        return cleaned_data

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'required': True})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'required': True})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'required': True}),
            'username': forms.TextInput(attrs={'class': 'form-input', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'required': True}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        # New signups default safely to Learner or Member, cannot self-assign Lead/Authority
        user.role = Role.LEARNER
        if commit:
            user.save()
        return user
