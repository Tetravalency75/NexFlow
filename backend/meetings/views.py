from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from accounts.models import User, Role
from accounts.permissions import lead_or_authority_required
from tasks.models import Task, TaskStatus, TaskPriority, RaciRole
from .models import (
    Meeting, MeetingMode, MeetingStatus, AttendanceResponse,
    AttendanceStatus, HostNotification, ActionItem, ActionItemStatus,
    MeetingMinutes
)
from .forms import MeetingForm, MeetingMinutesForm, AttendanceResponseForm, ActionItemForm

def get_visible_meetings(user):
    """
    Returns meetings accessible to the user:
    - Authority & Lead: all meetings
    - Member & Learner: meetings where they are attendees or host
    """
    if user.is_authority or user.is_lead:
        return Meeting.objects.all()
    return Meeting.objects.filter(attendees=user).distinct()

def user_can_manage_meeting(user, meeting):
    """
    Authority can manage all meetings.
    Lead can manage meetings they host.
    Learners and Members cannot manage meetings.
    """
    if not (user.is_authority or user.is_lead):
        return False
    if user.is_authority:
        return True
    return meeting.host == user

def user_can_access_meeting(user, meeting):
    """
    Checks if a user is permitted to view details and links for a meeting.
    """
    if user.is_authority or user.is_lead:
        return True
    if meeting.host == user:
        return True
    return meeting.attendees.filter(id=user.id).exists()

@login_required
def meetings_view(request):
    user = request.user
    today = timezone.now().date()
    qs = get_visible_meetings(user)

    upcoming_meetings = qs.filter(date__gte=today).exclude(status=MeetingStatus.CANCELLED).order_by('date', 'start_time')
    past_meetings = qs.filter(date__lt=today).order_by('-date', '-start_time')
    cancelled_meetings = qs.filter(status=MeetingStatus.CANCELLED).order_by('-date', '-start_time')

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
    if user.is_authority or user.is_lead:
        all_action_items = ActionItem.objects.all().select_related('meeting', 'owner')
    else:
        all_action_items = ActionItem.objects.filter(owner=user).select_related('meeting', 'owner')

    active_tab = request.GET.get('tab', 'upcoming')

    context = {
        'upcoming_meetings': upcoming_meetings,
        'past_meetings': past_meetings,
        'cancelled_meetings': cancelled_meetings,
        'notifications': notifications,
        'my_responses': my_responses,
        'action_items': all_action_items,
        'active_tab': active_tab,
        'meeting_form': MeetingForm() if user.can_create_meetings else None,
        'attendance_form': AttendanceResponseForm(),
        'action_form': ActionItemForm(),
        'minutes_form': MeetingMinutesForm(),
        'team_members': User.objects.filter(is_active=True),
    }
    return render(request, 'meetings.html', context)

@login_required
def meetings_upcoming_view(request):
    user = request.user
    today = timezone.now().date()
    qs = get_visible_meetings(user).filter(date__gte=today).exclude(status=MeetingStatus.CANCELLED).order_by('date', 'start_time')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        data = [{
            'id': m.id,
            'title': m.title,
            'date': m.date.isoformat(),
            'start_time': m.start_time.strftime('%H:%M'),
            'end_time': m.end_time.strftime('%H:%M') if m.end_time else None,
            'mode': m.mode,
            'meeting_link': m.meeting_link if user_can_access_meeting(user, m) else None,
            'location': m.location,
            'host': m.host.display_name,
            'attendees_count': m.attendees.count(),
        } for m in qs]
        return JsonResponse({'success': True, 'meetings': data})

    return redirect('/meetings/?tab=upcoming')

@login_required
def meetings_past_view(request):
    user = request.user
    today = timezone.now().date()
    qs = get_visible_meetings(user).filter(date__lt=today).order_by('-date', '-start_time')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        data = [{
            'id': m.id,
            'title': m.title,
            'date': m.date.isoformat(),
            'start_time': m.start_time.strftime('%H:%M'),
            'end_time': m.end_time.strftime('%H:%M') if m.end_time else None,
            'mode': m.mode,
            'host': m.host.display_name,
            'minutes': m.minutes or (m.official_minutes.discussion_summary if hasattr(m, 'official_minutes') else ''),
        } for m in qs]
        return JsonResponse({'success': True, 'meetings': data})

    return redirect('/meetings/?tab=past')

@login_required
def meeting_detail_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    # STRICT ACCESS ENFORCEMENT: unauthorized users cannot view meeting details or links
    if not user_can_access_meeting(user, meeting):
        return HttpResponseForbidden("Permission Denied: You are not authorized to access this meeting.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        official_min = getattr(meeting, 'official_minutes', None)
        return JsonResponse({
            'success': True,
            'id': meeting.id,
            'title': meeting.title,
            'description': meeting.description,
            'agenda': meeting.agenda,
            'date': meeting.date.isoformat(),
            'start_time': meeting.start_time.strftime('%H:%M'),
            'end_time': meeting.end_time.strftime('%H:%M') if meeting.end_time else None,
            'mode': meeting.mode,
            'location': meeting.location,
            'meeting_link': meeting.meeting_link,
            'status': meeting.status,
            'host': {'id': meeting.host.id, 'name': meeting.host.display_name, 'role': meeting.host.role},
            'attendees': [{'id': a.id, 'name': a.display_name, 'role': a.role} for a in meeting.attendees.all()],
            'minutes': {
                'discussion_summary': official_min.discussion_summary if official_min else '',
                'decisions_made': official_min.decisions_made if official_min else '',
                'notes': official_min.notes if official_min else '',
                'raw': meeting.minutes,
            },
            'action_items': [{
                'id': item.id,
                'title': item.title,
                'description': item.description,
                'owner': item.owner.display_name,
                'status': item.status,
                'due_date': item.due_date.isoformat() if item.due_date else None,
                'is_converted': item.is_converted,
            } for item in meeting.action_items.all()],
        })

    user_resp = AttendanceResponse.objects.filter(meeting=meeting, attendee=user).first()
    can_manage = user_can_manage_meeting(user, meeting)
    official_minutes = getattr(meeting, 'official_minutes', None)

    context = {
        'meeting': meeting,
        'can_manage': can_manage,
        'user_resp': user_resp,
        'official_minutes': official_minutes,
        'attendance_form': AttendanceResponseForm(instance=user_resp),
        'minutes_form': MeetingMinutesForm(instance=official_minutes),
        'action_form': ActionItemForm(),
        'team_members': User.objects.filter(is_active=True),
    }
    return render(request, 'meeting_detail.html', context)

@login_required
def meeting_create_view(request):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Only Authorities and Leads (Core Team) can schedule meetings.
    Members and Learners receive HTTP 403 Forbidden.
    """
    user = request.user
    if not user.can_create_meetings:
        return HttpResponseForbidden("Permission Denied: Only Leads and Authorities can schedule meetings.")

    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.host = user # Strictly server-determined host
            meeting.status = MeetingStatus.SCHEDULED
            meeting.clean()
            meeting.save()
            form.save_m2m()

            # Host is automatically included in attendees
            meeting.attendees.add(user)

            messages.success(request, f"Meeting '{meeting.title}' scheduled successfully for {meeting.date}.")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'meeting_id': meeting.id, 'title': meeting.title})
            return redirect('meetings')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            messages.error(request, "Failed to schedule meeting. Please check form validation errors.")
    return redirect('meetings')

@login_required
def meeting_edit_view(request, meeting_id):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Only Authorities or authorized meeting organizers (host) can edit meeting details.
    Learners and Members receive HTTP 403 Forbidden.
    Modifications are rejected on GET requests.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if not user_can_manage_meeting(user, meeting):
        return HttpResponseForbidden("Permission Denied: You are not authorized to edit this meeting.")

    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            meeting = form.save(commit=False)
            # Prevent unauthorized modification of host
            if not user.is_authority:
                meeting.host = user
            meeting.clean()
            meeting.save()
            form.save_m2m()
            messages.success(request, f"Meeting '{meeting.title}' updated successfully.")
            return redirect('meeting_detail', meeting_id=meeting.id)
        else:
            messages.error(request, "Failed to update meeting. Please check validation errors.")
    else:
        form = MeetingForm(instance=meeting)

    context = {
        'meeting': meeting,
        'form': form,
    }
    return render(request, 'meeting_edit.html', context)

@login_required
def meeting_cancel_view(request, meeting_id):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Cancels a meeting.
    Destructive operations MUST use POST. GET requests return HTTP 405 Method Not Allowed.
    Only Authorities or authorized meeting hosts can cancel meetings.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'], "Cancellation must be submitted via POST request.")

    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if not user_can_manage_meeting(user, meeting):
        return HttpResponseForbidden("Permission Denied: You are not authorized to cancel this meeting.")

    meeting.status = MeetingStatus.CANCELLED
    meeting.save(update_fields=['status', 'updated_at'])
    messages.success(request, f"Meeting '{meeting.title}' has been cancelled.")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'status': meeting.status})
    return redirect('meetings')

@login_required
def meeting_join_view(request, meeting_id):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Allows authorized participants to join an active virtual meeting.
    Unauthorized users receive HTTP 403 Forbidden.
    Cancelled meetings cannot be joined.
    Accurately records that the participant accessed the join link without
    falsely claiming confirmed official attendance.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if not user_can_access_meeting(user, meeting):
        return HttpResponseForbidden("Permission Denied: You are not authorized to join this meeting.")

    if meeting.status == MeetingStatus.CANCELLED:
        messages.error(request, "This meeting has been cancelled.")
        return redirect('meetings')

    if meeting.mode != MeetingMode.VIRTUAL or not meeting.meeting_link:
        messages.warning(request, "No virtual video conference link is configured for this meeting.")
        return redirect('meetings')

    # Record link join click without marking confirmed official attendance
    AttendanceResponse.objects.update_or_create(
        meeting=meeting,
        attendee=user,
        defaults={
            'joined_via_link': True,
            'joined_at': timezone.now(),
        }
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'meeting_link': meeting.meeting_link})

    return redirect(meeting.meeting_link)

@login_required
def meeting_minutes_view(request, meeting_id):
    """
    Views or records official meeting minutes:
    - GET: Viewing permitted to all authorized meeting participants.
    - POST: Only Authority, Lead, or meeting host can record or update official minutes.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if not user_can_access_meeting(user, meeting):
        return HttpResponseForbidden("Permission Denied: You are not authorized to access this meeting.")

    if request.method == 'POST':
        if not (user.is_authority or user.is_lead or meeting.host == user):
            return HttpResponseForbidden("Permission Denied: Only authorized leads and authorities can record official minutes.")

        discussion_summary = request.POST.get('discussion_summary', '').strip()
        decisions_made = request.POST.get('decisions_made', '').strip()
        notes = request.POST.get('notes', '').strip()
        raw_minutes = request.POST.get('minutes', '').strip()

        if raw_minutes and not discussion_summary:
            discussion_summary = raw_minutes

        min_obj, created = MeetingMinutes.objects.update_or_create(
            meeting=meeting,
            defaults={
                'discussion_summary': discussion_summary,
                'decisions_made': decisions_made,
                'notes': notes,
                'created_by': user,
            }
        )

        # Sync text field on Meeting for backwards compatibility
        combined_text = []
        if discussion_summary:
            combined_text.append(f"Summary: {discussion_summary}")
        if decisions_made:
            combined_text.append(f"Decisions: {decisions_made}")
        if notes:
            combined_text.append(f"Notes: {notes}")

        meeting.minutes = "\n\n".join(combined_text) if combined_text else raw_minutes
        meeting.save(update_fields=['minutes'])

        messages.success(request, f"Official minutes recorded for '{meeting.title}'.")
        return redirect('meeting_detail', meeting_id=meeting.id)

    # GET response
    if hasattr(meeting, 'official_minutes'):
        official = meeting.official_minutes
        data = {
            'discussion_summary': official.discussion_summary,
            'decisions_made': official.decisions_made,
            'notes': official.notes,
            'created_by': official.created_by.display_name,
            'created_at': official.created_at.isoformat(),
        }
    else:
        data = {'discussion_summary': meeting.minutes, 'decisions_made': '', 'notes': '', 'created_by': ''}

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'success': True, 'minutes': data})

    return redirect('meeting_detail', meeting_id=meeting.id)

@login_required
def meeting_action_items_view(request, meeting_id):
    """
    Lists or creates action items for a meeting.
    Creation/assignment is strictly restricted to Authorities and Leads.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if not user_can_access_meeting(user, meeting):
        return HttpResponseForbidden("Permission Denied: You are not authorized to access this meeting.")

    if request.method == 'POST':
        if not (user.can_assign_tasks or meeting.host == user):
            return HttpResponseForbidden("Permission Denied: Only meeting host or authorized leads can add action items.")

        form = ActionItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.meeting = meeting
            item.created_by = user
            item.save()
            messages.success(request, f"Action item '{item.title or item.description}' assigned to {item.owner.display_name}.")
        else:
            messages.error(request, "Failed to create action item. Please check errors.")
        return redirect('meeting_detail', meeting_id=meeting.id)

    # GET: return list
    items = [{
        'id': it.id,
        'title': it.title,
        'description': it.description,
        'owner': it.owner.display_name,
        'status': it.status,
        'due_date': it.due_date.isoformat() if it.due_date else None,
        'is_converted': it.is_converted,
    } for it in meeting.action_items.all()]

    return JsonResponse({'success': True, 'action_items': items})

@login_required
def action_item_create_view(request, meeting_id):
    """Convenience alias route matching existing form POST endpoint."""
    return meeting_action_items_view(request, meeting_id)

@login_required
def action_item_status_view(request, item_id):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Updates status of an action item.
    - Authorities and Leads can update any action item.
    - Assigned owner can update the status of their OWN action item.
    - Users CANNOT modify another user's action item (returns HTTP 403 Forbidden).
    - Destructive operations require POST.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'], "Status update must be submitted via POST request.")

    item = get_object_or_404(ActionItem, id=item_id)
    user = request.user

    can_modify = user.is_authority or user.is_lead or item.owner == user
    if not can_modify:
        return HttpResponseForbidden("Permission Denied: You cannot modify another user's action item.")

    new_status = request.POST.get('status')
    if new_status in [ActionItemStatus.TODO, ActionItemStatus.IN_PROGRESS, ActionItemStatus.DONE]:
        item.status = new_status
        item.save(update_fields=['status', 'updated_at'])

        # Synchronize linked Task if converted
        if item.converted_task:
            item.converted_task.status = new_status
            item.converted_task.save(update_fields=['status', 'updated_at'])

        messages.success(request, f"Action item status updated to {new_status}.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'status': item.status})

    return redirect('meetings')

@login_required
def action_item_convert_view(request, item_id):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Converts an Action Item into a Task.
    Only Authorities and Leads can assign tasks.
    PREVENTS DUPLICATION: Idempotently checks if action item was already converted.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'], "Conversion must be submitted via POST request.")

    item = get_object_or_404(ActionItem, id=item_id)
    user = request.user

    if not user.can_assign_tasks:
        return HttpResponseForbidden("Permission Denied: Only Authorities and Leads can convert action items into tasks.")

    if item.is_converted:
        messages.info(request, f"Action item was already converted into Task '{item.converted_task.title}'. Duplicate prevented.")
        return redirect('meetings')

    task_title = f"[Action Item] {item.title or item.description[:50]}"
    task = Task.objects.create(
        title=task_title,
        description=f"Generated from meeting '{item.meeting.title}' held on {item.meeting.date}.\nDescription: {item.description}\nOriginal Action Item ID: {item.id}",
        status=item.status if item.status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE] else TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        raci_role=RaciRole.RESPONSIBLE,
        created_by=user,
        assigned_to=item.owner,
        due_date=item.due_date,
    )

    item.is_converted = True
    item.converted_task = task
    item.save(update_fields=['is_converted', 'converted_task', 'updated_at'])

    messages.success(request, f"Converted action item into Task '{task.title}' for {task.assigned_to.display_name} without duplication.")
    return redirect('meetings')

@login_required
def attendance_submit_view(request, meeting_id):
    """
    Records an attendee's RSVP (Attending or Absent with reason).
    Prevents modifying other users' responses.
    Sends an in-app notification to the host when someone reports absent.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    user = request.user

    if not user_can_access_meeting(user, meeting):
        return HttpResponseForbidden("Permission Denied: You are not authorized to RSVP for this meeting.")

    if request.method == 'POST':
        status = request.POST.get('status', AttendanceStatus.ATTENDING)
        absence_reason = request.POST.get('absence_reason', '').strip()

        response, created = AttendanceResponse.objects.update_or_create(
            meeting=meeting,
            attendee=user,
            defaults={
                'status': status,
                'absence_reason': absence_reason,
            }
        )

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
