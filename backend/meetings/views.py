from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from accounts.models import User
from accounts.permissions import lead_or_authority_required
from tasks.models import Task, TaskStatus, TaskPriority, RaciRole
from .models import Meeting, AttendanceResponse, AttendanceStatus, HostNotification, ActionItem
from .forms import MeetingForm, AttendanceResponseForm, ActionItemForm

@login_required
def meetings_view(request):
    user = request.user
    today = timezone.now().date()

    # Scope meetings: Authorities and Leads see all team meetings; Members/Learners see invited or hosted meetings
    if user.is_authority or user.is_lead:
        upcoming_meetings = Meeting.objects.filter(date__gte=today).order_by('date', 'start_time')
        past_meetings = Meeting.objects.filter(date__lt=today).order_by('-date', '-start_time')
    else:
        upcoming_meetings = Meeting.objects.filter(attendees=user, date__gte=today).order_by('date', 'start_time')
        past_meetings = Meeting.objects.filter(attendees=user, date__lt=today).order_by('-date', '-start_time')

    # Absence notifications visible to meeting hosts and Authorities
    if user.is_authority:
        notifications = HostNotification.objects.all()[:10]
    elif user.is_lead:
        notifications = HostNotification.objects.filter(host=user)[:10]
    else:
        notifications = []

    # Map current user's attendance status per meeting
    my_responses = {
        resp.meeting_id: resp
        for resp in AttendanceResponse.objects.filter(attendee=user)
    }

    # Action items across visible meetings
    all_action_items = ActionItem.objects.all().select_related('meeting', 'owner') if (user.is_authority or user.is_lead) else ActionItem.objects.filter(owner=user).select_related('meeting', 'owner')

    context = {
        'upcoming_meetings': upcoming_meetings,
        'past_meetings': past_meetings,
        'notifications': notifications,
        'my_responses': my_responses,
        'action_items': all_action_items,
        'meeting_form': MeetingForm() if user.can_create_meetings else None,
        'attendance_form': AttendanceResponseForm(),
        'action_form': ActionItemForm(),
    }
    return render(request, 'meetings.html', context)

@login_required
def meeting_create_view(request):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Only Authorities and Leads may schedule/host meetings.
    """
    user = request.user
    if not user.can_create_meetings:
        return HttpResponseForbidden("Permission Denied: Only Leads and Authorities can schedule meetings.")

    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.host = user
            meeting.save()
            form.save_m2m() # Save attendee relations

            # Host is automatically included in attendees
            meeting.attendees.add(user)

            messages.success(request, f"Meeting '{meeting.title}' scheduled successfully for {meeting.date}.")
            return redirect('meetings')
        else:
            messages.error(request, "Failed to schedule meeting. Please check form validation errors.")
    return redirect('meetings')

@login_required
def attendance_submit_view(request, meeting_id):
    """
    Records an attendee's attendance or absence reason.
    Prevents modifying other users' responses.
    Sends an in-app notification to the host when someone reports absent.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if request.method == 'POST':
        status = request.POST.get('status', AttendanceStatus.ATTENDING)
        absence_reason = request.POST.get('absence_reason', '').strip()

        # Save or update user attendance response
        response, created = AttendanceResponse.objects.update_or_create(
            meeting=meeting,
            attendee=user,
            defaults={
                'status': status,
                'absence_reason': absence_reason,
            }
        )

        # Notify host if attendee cannot attend
        if status == AttendanceStatus.ABSENT:
            HostNotification.objects.create(
                host=meeting.host,
                meeting=meeting,
                attendee=user,
                reason=absence_reason if absence_reason else "No specific absence reason provided."
            )
            messages.warning(request, f"Reported absence for '{meeting.title}'. Notification sent to host {meeting.host.display_name}.")
        else:
            messages.success(request, f"Marked as Attending for '{meeting.title}'.")

    return redirect('meetings')

@login_required
def meeting_minutes_view(request, meeting_id):
    """
    Records or updates meeting notes/minutes.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if not (user.is_authority or user.is_lead or meeting.host == user):
        return HttpResponseForbidden("Permission Denied: You are not authorized to record minutes for this meeting.")

    if request.method == 'POST':
        minutes = request.POST.get('minutes', '').strip()
        meeting.minutes = minutes
        meeting.save()
        messages.success(request, f"Minutes recorded for '{meeting.title}'.")

    return redirect('meetings')

@login_required
def action_item_create_view(request, meeting_id):
    """
    Creates a new action item under the specified meeting.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if not (user.is_authority or user.is_lead or meeting.host == user):
        return HttpResponseForbidden("Permission Denied: Only meeting host or authorized leads can add action items.")

    if request.method == 'POST':
        form = ActionItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.meeting = meeting
            item.save()
            messages.success(request, f"Action item '{item.description}' assigned to {item.owner.display_name}.")
        else:
            messages.error(request, "Failed to create action item.")
    return redirect('meetings')

@login_required
def action_item_convert_view(request, item_id):
    """
    Converts an Action Item into a Task.
    PREVENTS DUPLICATION: Checks if action item is already converted!
    Links the generated Task back to originating meeting and action item.
    """
    item = get_object_or_404(ActionItem, id=item_id)
    user = request.user

    if not user.can_assign_tasks:
        return HttpResponseForbidden("Permission Denied: Only Authorities and Leads can convert action items into tasks.")

    if item.is_converted:
        messages.info(request, f"Action item was already converted into Task '{item.converted_task.title}'. Duplicate prevented.")
        return redirect('meetings')

    # Create corresponding Task
    task = Task.objects.create(
        title=f"[Action Item] {item.description}",
        description=f"Generated from meeting '{item.meeting.title}' held on {item.meeting.date}.\nOriginal Action Item ID: {item.id}",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        raci_role=RaciRole.RESPONSIBLE,
        created_by=user,
        assigned_to=item.owner,
        due_date=item.due_date,
    )

    # Link back to action item and mark converted
    item.is_converted = True
    item.converted_task = task
    item.save()

    messages.success(request, f"Converted action item into Task '{task.title}' for {task.assigned_to.display_name} without duplication.")
    return redirect('meetings')
