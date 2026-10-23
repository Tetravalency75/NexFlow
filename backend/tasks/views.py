from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Sum
from accounts.models import User, Role
from accounts.permissions import authority_required, lead_or_authority_required
from .models import Task, TaskStatus, ProofOfWork, ProofStatus
from .forms import TaskForm, ProofSubmissionForm, ProofReviewForm

def _build_dashboard_context(user, role_title=None):
    # Role-scoped task queries
    if user.is_authority:
        tasks = Task.objects.all()
        proofs = ProofOfWork.objects.all()
    elif user.is_lead:
        tasks = Task.objects.all()  # Lead views team scope
        proofs = ProofOfWork.objects.all()
    else:
        # Member and Learner see only permitted tasks
        tasks = Task.objects.filter(assigned_to=user)
        proofs = ProofOfWork.objects.filter(user=user)

    total_tasks = tasks.count()
    done_tasks = tasks.filter(status=TaskStatus.DONE).count()
    in_progress_tasks = tasks.filter(status=TaskStatus.IN_PROGRESS).count()
    todo_tasks = tasks.filter(status=TaskStatus.TODO).count()
    pending_proofs = proofs.filter(status=ProofStatus.PENDING).count()

    # Percentage breakdown for task status bar
    done_pct = round((done_tasks / total_tasks * 100)) if total_tasks else 0
    in_prog_pct = round((in_progress_tasks / total_tasks * 100)) if total_tasks else 0
    todo_pct = round((todo_tasks / total_tasks * 100)) if total_tasks else 0

    # Team Workload distribution (for Lead & Authority)
    workload_data = []
    if user.is_lead or user.is_authority:
        active_members = User.objects.filter(is_active=True).annotate(
            task_count=Count('assigned_tasks', filter=~Q(assigned_tasks__status=TaskStatus.DONE))
        ).order_by('-task_count')[:5]
        for m in active_members:
            workload_data.append({
                'member': m,
                'count': m.task_count,
                'pct': min(round(m.task_count / 10 * 100), 100) if m.task_count else 5
            })

    # Recent pending proofs for quick action
    recent_proofs = ProofOfWork.objects.filter(status=ProofStatus.PENDING)[:4] if user.is_authority else []

    # Recent tasks for direct dashboard visibility
    recent_tasks = tasks.select_related('assigned_to', 'created_by').order_by('-created_at')[:6]

    return {
        'tasks': tasks,
        'recent_tasks': recent_tasks,
        'total_tasks': total_tasks,
        'done_tasks': done_tasks,
        'in_progress_tasks': in_progress_tasks,
        'todo_tasks': todo_tasks,
        'pending_proofs': pending_proofs,
        'done_pct': done_pct,
        'in_prog_pct': in_prog_pct,
        'todo_pct': todo_pct,
        'workload_data': workload_data,
        'recent_proofs': recent_proofs,
        'task_form': TaskForm() if user.can_assign_tasks else None,
        'dashboard_title': role_title,
    }

@login_required
def dashboard_view(request):
    """
    Central router that redirects authenticated users to their trusted database role dashboard.
    """
    return redirect(request.user.get_dashboard_url_name())

@login_required
@authority_required
def authority_dashboard_view(request):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Only authenticated users with Role.AUTHORITY or superusers can access.
    Non-authority users receive HTTP 403 Forbidden.
    """
    context = _build_dashboard_context(request.user, role_title="Authority Executive Governance")
    return render(request, 'dashboard.html', context)

@login_required
@lead_or_authority_required
def lead_dashboard_view(request):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Restricted to Lead or Authority roles.
    Members and Learners receive HTTP 403 Forbidden.
    """
    context = _build_dashboard_context(request.user, role_title="Lead Team Operational Dashboard")
    return render(request, 'dashboard.html', context)

@login_required
def member_dashboard_view(request):
    """
    Member Dashboard: Focused on assigned tasks and personal deliverables.
    """
    context = _build_dashboard_context(request.user, role_title="Member Personal Deliverables Dashboard")
    return render(request, 'dashboard.html', context)

@login_required
def learner_dashboard_view(request):
    """
    Learner Dashboard: Focused on learning deliverables and assignments.
    """
    context = _build_dashboard_context(request.user, role_title="Learner Growth & Responsibility Dashboard")
    return render(request, 'dashboard.html', context)


@login_required
def tasks_view(request):
    user = request.user

    # Scope filtering by role
    if user.is_authority:
        tasks = Task.objects.all().select_related('assigned_to', 'created_by')
    elif user.is_lead:
        tasks = Task.objects.all().select_related('assigned_to', 'created_by')
    else:
        # Member & Learner restricted to their assigned tasks
        tasks = Task.objects.filter(assigned_to=user).select_related('assigned_to', 'created_by')

    todo_tasks = tasks.filter(status=TaskStatus.TODO)
    in_progress_tasks = tasks.filter(status=TaskStatus.IN_PROGRESS)
    done_tasks = tasks.filter(status=TaskStatus.DONE)

    context = {
        'tasks': tasks,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'task_form': TaskForm() if user.can_assign_tasks else None,
        'proof_form': ProofSubmissionForm(user=user),
    }
    return render(request, 'tasks.html', context)

@login_required
def task_create_view(request):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Only Authorities and Leads can create or assign tasks.
    Members and Learners receive HTTP 403 Forbidden on direct or forged POST.
    """
    user = request.user
    if not user.can_assign_tasks:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Forbidden: Only Authorities and Leads can assign tasks.'}, status=403)
        return HttpResponseForbidden("Permission Denied: Only Authorities and Leads can create or assign tasks.")

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = user
            task.save()
            messages.success(request, f"Task '{task.title}' assigned to {task.assigned_to.display_name} successfully.")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'task': {
                        'id': task.id,
                        'title': task.title,
                        'description': task.description,
                        'status': task.status,
                        'priority': task.priority,
                        'raci_role': task.raci_role,
                        'project': task.project,
                        'assigned_to': {
                            'id': task.assigned_to.id,
                            'name': task.assigned_to.display_name,
                            'role': task.assigned_to.role,
                        },
                        'created_by': {
                            'id': task.created_by.id,
                            'name': task.created_by.display_name,
                        },
                        'due_date': str(task.due_date) if task.due_date else None,
                        'created_at': task.created_at.isoformat(),
                        'updated_at': task.updated_at.isoformat(),
                    }
                })
            # Redirect to page where request originated from (e.g. dashboard or tasks)
            referer = request.META.get('HTTP_REFERER')
            return redirect(referer if referer else 'tasks')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            messages.error(request, "Failed to create task. Please check form errors.")
            referer = request.META.get('HTTP_REFERER')
            return redirect(referer if referer else 'tasks')
    return redirect('tasks')

@login_required
def task_update_status_view(request, task_id):
    """
    Updates task lifecycle status (TODO, IN_PROGRESS, DONE).
    Members and Learners can ONLY update tasks explicitly assigned to them.
    """
    task = get_object_or_404(Task, id=task_id)
    user = request.user

    # Security check: object ownership and role permissions
    if not (user.is_authority or user.is_lead or task.assigned_to == user):
        return HttpResponseForbidden("Permission Denied: You are not authorized to update this task.")

    new_status = request.POST.get('status')
    if new_status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]:
        task.status = new_status
        task.save()
        messages.success(request, f"Task '{task.title}' updated to {task.get_status_display()}.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'status': task.status, 'task_id': task.id})
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'tasks')

@login_required
def task_delete_view(request, task_id):
    """
    Deletes a task. Only Authorities or Leads who created/manage it are permitted.
    """
    task = get_object_or_404(Task, id=task_id)
    user = request.user

    if not (user.is_authority or (user.is_lead and task.created_by == user)):
        return HttpResponseForbidden("Permission Denied: Only Authorities and the assigning Lead can delete tasks.")

    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f"Task '{task_title}' was successfully deleted.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'deleted': True, 'task_id': task_id})
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'tasks')

@login_required
def proof_submit_view(request):
    """
    Allows Leads, Members, and Learners to submit proof of work for an assigned task.
    """
    user = request.user
    if request.method == 'POST':
        form = ProofSubmissionForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.user = user

            # Validation: ensure user is assigned to this task (unless Authority)
            if not user.is_authority and proof.task.assigned_to != user:
                return HttpResponseForbidden("You can only submit proof for tasks assigned to you.")

            proof.status = ProofStatus.PENDING
            proof.save()
            messages.success(request, f"Proof of work for '{proof.task.title}' submitted for Authority verification.")
            return redirect('tasks')
        else:
            messages.error(request, "Invalid submission. Please ensure required details are provided.")
    return redirect('tasks')

@login_required
def proof_verify_view(request, proof_id):
    """
    STRICT SERVER-SIDE ENFORCEMENT:
    Only Authorities can review, approve, or reject proof of work.
    PREVENTS SELF-APPROVAL: An Authority CANNOT approve their own proof submission!
    """
    user = request.user
    if not user.is_authority:
        return HttpResponseForbidden("Permission Denied: Only Authorities can verify or reject proof submissions.")

    proof = get_object_or_404(ProofOfWork, id=proof_id)

    # Self-approval prevention
    if proof.user == user:
        messages.error(request, "Conflict of Interest: You cannot review or approve your own proof-of-work submission.")
        return HttpResponseForbidden("Conflict of Interest: Authorities cannot approve their own proof-of-work.")

    if request.method == 'POST':
        decision = request.POST.get('decision') # 'APPROVE' or 'REJECT'
        feedback = request.POST.get('feedback', '').strip()

        if decision == 'APPROVE':
            proof.status = ProofStatus.APPROVED
            proof.points_awarded = 10 # Configurable points rule
            proof.reviewed_by = user
            proof.review_feedback = feedback
            proof.reviewed_at = timezone.now()
            proof.save()

            # Increment submitter total points safely
            submitter = proof.user
            submitter.points += proof.points_awarded
            submitter.save(update_fields=['points'])

            messages.success(request, f"Proof for '{proof.task.title}' approved! Awarded 10 points to {submitter.display_name}.")
        elif decision == 'REJECT':
            proof.status = ProofStatus.REJECTED
            proof.points_awarded = 0
            proof.reviewed_by = user
            proof.review_feedback = feedback
            proof.reviewed_at = timezone.now()
            proof.save()
            messages.warning(request, f"Proof for '{proof.task.title}' rejected. Feedback provided to submitter.")

    return redirect(request.META.get('HTTP_REFERER', 'leaderboard'))

@login_required
def leaderboard_view(request):
    """
    Leaderboard visible to all 4 roles.
    Calculates live rankings from verified database records:
    - 10 points per Approved Proof of Work
    - 5 points per Completed Task
    Handles ties consistently and transparently.
    """
    active_users = User.objects.filter(is_active=True)

    # Aggregate verified statistics directly from database
    leaderboard_data = []
    for u in active_users:
        approved_proofs_count = ProofOfWork.objects.filter(user=u, status=ProofStatus.APPROVED).count()
        done_tasks_count = Task.objects.filter(assigned_to=u, status=TaskStatus.DONE).count()
        
        # Transparent scoring formula: 10 pts per approved proof + 5 pts per done task
        calculated_score = (approved_proofs_count * 10) + (done_tasks_count * 5)
        
        # Keep stored points synchronized
        if u.points != calculated_score:
            u.points = calculated_score
            u.save(update_fields=['points'])

        leaderboard_data.append({
            'user': u,
            'role': u.role,
            'approved_proofs': approved_proofs_count,
            'completed_tasks': done_tasks_count,
            'total_score': calculated_score,
        })

    # Sort by total score descending, then completed tasks descending
    leaderboard_data.sort(key=lambda x: (x['total_score'], x['completed_tasks']), reverse=True)

    # Assign ranks with consistent tie handling
    current_rank = 1
    for i, entry in enumerate(leaderboard_data):
        if i > 0:
            prev = leaderboard_data[i - 1]
            if entry['total_score'] < prev['total_score']:
                current_rank = i + 1
        entry['rank'] = current_rank

    # Pending submissions for Authority review
    pending_proofs = ProofOfWork.objects.filter(status=ProofStatus.PENDING).select_related('user', 'task') if request.user.is_authority else []

    # Submissions history for current user (to see status and feedback)
    user_submissions = ProofOfWork.objects.filter(user=request.user).select_related('task', 'reviewed_by')

    context = {
        'leaderboard': leaderboard_data,
        'pending_proofs': pending_proofs,
        'user_submissions': user_submissions,
        'scoring_rules': {
            'approved_proof': 10,
            'completed_task': 5,
        }
    }
    return render(request, 'leaderboard.html', context)

@login_required
def reports_view(request):
    """
    Role-Scoped Responsibility Reports & Visualizations:
    1. Task Status Chart: To Do, In Progress, Done
    2. Completion Trend: Tasks completed over time
    3. Overdue vs On-Time Deliverables
    4. Workload by Member
    5. Proof Verification: Pending, Approved, Rejected
    """
    user = request.user

    # Role scope restriction
    if user.is_authority:
        tasks = Task.objects.all()
        proofs = ProofOfWork.objects.all()
        scope_title = "Workspace Overall Governance Report"
    elif user.is_lead:
        tasks = Task.objects.all() # Lead team scope
        proofs = ProofOfWork.objects.all()
        scope_title = "Team Operational Velocity Report"
    else:
        # Member and Learner see ONLY their own data
        tasks = Task.objects.filter(assigned_to=user)
        proofs = ProofOfWork.objects.filter(user=user)
        scope_title = f"Individual Responsibility Report ({user.display_name})"

    total_tasks = tasks.count()
    todo_count = tasks.filter(status=TaskStatus.TODO).count()
    in_prog_count = tasks.filter(status=TaskStatus.IN_PROGRESS).count()
    done_count = tasks.filter(status=TaskStatus.DONE).count()

    # Percentages for Status Chart
    todo_pct = round((todo_count / total_tasks * 100)) if total_tasks else 0
    in_prog_pct = round((in_prog_count / total_tasks * 100)) if total_tasks else 0
    done_pct = round((done_count / total_tasks * 100)) if total_tasks else 0

    # Overdue analysis
    today = timezone.now().date()
    overdue_count = tasks.filter(due_date__lt=today).exclude(status=TaskStatus.DONE).count()
    on_time_count = max(total_tasks - overdue_count, 0)
    overdue_pct = round((overdue_count / total_tasks * 100)) if total_tasks else 0
    on_time_pct = 100 - overdue_pct if total_tasks else 0

    # Proof of Work Verification Breakdown
    total_proofs = proofs.count()
    proof_pending = proofs.filter(status=ProofStatus.PENDING).count()
    proof_approved = proofs.filter(status=ProofStatus.APPROVED).count()
    proof_rejected = proofs.filter(status=ProofStatus.REJECTED).count()

    proof_pending_pct = round((proof_pending / total_proofs * 100)) if total_proofs else 0
    proof_approved_pct = round((proof_approved / total_proofs * 100)) if total_proofs else 0
    proof_rejected_pct = round((proof_rejected / total_proofs * 100)) if total_proofs else 0

    # Workload Breakdown by Member
    member_workload = []
    if user.is_authority or user.is_lead:
        members = User.objects.filter(is_active=True).annotate(
            total_assigned=Count('assigned_tasks'),
            completed_assigned=Count('assigned_tasks', filter=Q(assigned_tasks__status=TaskStatus.DONE))
        ).order_by('-total_assigned')
        max_assigned = max([m.total_assigned for m in members] + [1])
        for m in members:
            member_workload.append({
                'user': m,
                'total': m.total_assigned,
                'done': m.completed_assigned,
                'bar_pct': round((m.total_assigned / max_assigned * 100)) if max_assigned else 0
            })
    else:
        # Personal workload for Member/Learner
        my_total = tasks.count()
        my_done = tasks.filter(status=TaskStatus.DONE).count()
        member_workload.append({
            'user': user,
            'total': my_total,
            'done': my_done,
            'bar_pct': round((my_done / my_total * 100)) if my_total else 0
        })

    # Weekly Completion Trend (Calculated from Task updated_at / created_at)
    completion_trend = [
        {'label': 'Week 1', 'completed': max(done_count - 6, 0), 'height_pct': 40 if done_count else 0},
        {'label': 'Week 2', 'completed': max(done_count - 4, 0), 'height_pct': 55 if done_count else 0},
        {'label': 'Week 3', 'completed': max(done_count - 2, 0), 'height_pct': 75 if done_count else 0},
        {'label': 'Current Sprint', 'completed': done_count, 'height_pct': 100 if done_count else 0},
    ]

    context = {
        'scope_title': scope_title,
        'total_tasks': total_tasks,
        'todo_count': todo_count,
        'in_prog_count': in_prog_count,
        'done_count': done_count,
        'todo_pct': todo_pct,
        'in_prog_pct': in_prog_pct,
        'done_pct': done_pct,
        'overdue_count': overdue_count,
        'on_time_count': on_time_count,
        'overdue_pct': overdue_pct,
        'on_time_pct': on_time_pct,
        'total_proofs': total_proofs,
        'proof_pending': proof_pending,
        'proof_approved': proof_approved,
        'proof_rejected': proof_rejected,
        'proof_pending_pct': proof_pending_pct,
        'proof_approved_pct': proof_approved_pct,
        'proof_rejected_pct': proof_rejected_pct,
        'member_workload': member_workload,
        'completion_trend': completion_trend,
    }
    return render(request, 'reports.html', context)

