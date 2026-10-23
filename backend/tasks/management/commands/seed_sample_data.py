from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from tasks.models import Task, TaskStatus, TaskPriority, RaciRole, ProofOfWork, ProofStatus
from meetings.models import Meeting, AttendanceResponse, AttendanceStatus, HostNotification, ActionItem
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seeds initial sample tasks, proofs, meetings, and action items for testing.'

    def handle(self, *args, **options):
        authority = User.objects.filter(username='alexa.authority').first()
        lead = User.objects.filter(username='alex.morgan').first()
        member = User.objects.filter(username='sarah.chen').first()
        learner = User.objects.filter(username='leo.learner').first()

        if not (authority and lead and member and learner):
            self.stdout.write(self.style.ERROR("Please run 'python manage.py seed_demo_accounts' first."))
            return

        today = timezone.now().date()

        # 1. Create sample Tasks
        task1, _ = Task.objects.get_or_create(
            title="Design Core Database Architecture & Schema",
            defaults={
                'description': "Establish normalized SQLite models for tasks, proof verification, and meeting minutes.",
                'status': TaskStatus.DONE,
                'priority': TaskPriority.HIGH,
                'raci_role': RaciRole.RESPONSIBLE,
                'created_by': lead,
                'assigned_to': member,
                'due_date': today - timedelta(days=2),
            }
        )

        task2, _ = Task.objects.get_or_create(
            title="Implement Role-Based Security Decorators",
            defaults={
                'description': "Enforce server-side permissions for Authority, Lead, Member, and Learner tiers.",
                'status': TaskStatus.IN_PROGRESS,
                'priority': TaskPriority.URGENT,
                'raci_role': RaciRole.ACCOUNTABLE,
                'created_by': authority,
                'assigned_to': lead,
                'due_date': today + timedelta(days=3),
            }
        )

        task3, _ = Task.objects.get_or_create(
            title="Responsive Sidebar CSS & Media Queries",
            defaults={
                'description': "Optimize tablet and mobile sidebar drawer and center NX brand emblem.",
                'status': TaskStatus.DONE,
                'priority': TaskPriority.MEDIUM,
                'raci_role': RaciRole.RESPONSIBLE,
                'created_by': lead,
                'assigned_to': learner,
                'due_date': today + timedelta(days=1),
            }
        )

        task4, _ = Task.objects.get_or_create(
            title="Responsibility Report Pure CSS Charts",
            defaults={
                'description': "Render task status, completion trends, and verification breakdowns without 3rd-party libs.",
                'status': TaskStatus.TODO,
                'priority': TaskPriority.HIGH,
                'raci_role': RaciRole.CONSULTED,
                'created_by': authority,
                'assigned_to': member,
                'due_date': today + timedelta(days=5),
            }
        )

        # 2. Create sample Proof of Work submissions
        proof1, _ = ProofOfWork.objects.get_or_create(
            task=task1,
            user=member,
            defaults={
                'description': "Completed SQLite schema migrations and registered all models in Django Admin. Tested integrity.",
                'proof_url': "https://github.com/nexflow/pull/42",
                'status': ProofStatus.APPROVED,
                'reviewed_by': authority,
                'review_feedback': "Excellent schema normalization and documentation in database-design.md.",
                'reviewed_at': timezone.now(),
                'points_awarded': 10,
            }
        )

        proof2, _ = ProofOfWork.objects.get_or_create(
            task=task3,
            user=learner,
            defaults={
                'description': "Fixed sidebar footer team-pill padding and centered NX logo across 72px and 260px widths.",
                'proof_url': "https://github.com/nexflow/commit/sidebar-fix",
                'status': ProofStatus.PENDING,
            }
        )

        # 3. Create sample Meeting
        meeting, _ = Meeting.objects.get_or_create(
            title="Sprint Planning & RACI Alignment",
            defaults={
                'agenda': "1. Review sprint deliverables\n2. Discuss proof-of-work workflow\n3. Assign action items",
                'date': today + timedelta(days=1),
                'start_time': timezone.now().time().replace(hour=14, minute=0, second=0),
                'meeting_link': "https://meet.google.com/nex-flow-sync",
                'host': lead,
                'minutes': "Meeting scheduled for sprint velocity review.",
            }
        )
        meeting.attendees.add(authority, lead, member, learner)

        # 4. Create Attendance response with absence reason from Learner
        AttendanceResponse.objects.get_or_create(
            meeting=meeting,
            attendee=member,
            defaults={'status': AttendanceStatus.ATTENDING}
        )
        AttendanceResponse.objects.get_or_create(
            meeting=meeting,
            attendee=learner,
            defaults={
                'status': AttendanceStatus.ABSENT,
                'absence_reason': "Scheduled academic exam during meeting time window."
            }
        )

        # 5. Create Host Notification for Alex Morgan (Lead)
        HostNotification.objects.get_or_create(
            host=lead,
            meeting=meeting,
            attendee=learner,
            defaults={
                'reason': "Scheduled academic exam during meeting time window.",
                'is_read': False,
            }
        )

        # 6. Create Action Item
        ActionItem.objects.get_or_create(
            meeting=meeting,
            description="Prepare automated unit test suite for role-based permissions",
            defaults={
                'owner': member,
                'due_date': today + timedelta(days=4),
                'is_converted': False,
            }
        )

        self.stdout.write(self.style.SUCCESS("Sample tasks, proofs, meetings, and notifications seeded successfully!"))
