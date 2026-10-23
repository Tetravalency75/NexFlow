from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from .forms import LoginForm, RegisterForm
from .models import User, Role

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            messages.success(request, f"Welcome back, {user.display_name}! Signed in as {user.role}.")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect('login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! Welcome to NEXFlow.")
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

@login_required
def settings_view(request):
    user = request.user
    if request.method == 'POST':
        # Safely update user profile attributes without allowing self-promoted role change
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        job_title = request.POST.get('job_title', '').strip()
        department = request.POST.get('department', '').strip()

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if job_title:
            user.job_title = job_title
        if department:
            user.department = department

        user.save()
        messages.success(request, "Profile preferences updated successfully.")
        return redirect('settings')

    return render(request, 'settings.html', {'user': user})

@login_required
def team_view(request):
    users = User.objects.all().order_by('role', 'first_name')
    return render(request, 'team.html', {'team_members': users})


