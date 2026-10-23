from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from accounts.models import User, Role
from tasks.models import Task, TaskStatus
from meetings.models import (
    Meeting, MeetingMode, MeetingStatus, AttendanceResponse,
    AttendanceStatus, HostNotification, ActionItem, ActionItemStatus,
    MeetingMinutes, validate_meeting_url
)

class MeetingGovernanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'Pass12345!'
        self.authority = User.objects.create_user(
            username='auth_host', email='auth_host@test.com', password=self.password, role=Role.AUTHORITY
        )
        self.lead = User.objects.create_user(
            username='lead_host', email='lead_host@test.com', password=self.password, role=Role.LEAD
        )
        self.member = User.objects.create_user(
            username='member_attendee', email='member_att@test.com', password=self.password, role=Role.MEMBER
        )
        self.other_member = User.objects.create_user(
            username='other_member', email='other_member@test.com', password=self.password, role=Role.MEMBER
        )
        self.learner = User.objects.create_user(
            username='learner_attendee', email='learner_att@test.com', password=self.password, role=Role.LEARNER
        )

        self.meeting_date = timezone.now().date() + timedelta(days=2)
        self.meeting = Meeting.objects.create(
            title="Sprint Planning Meeting",
            description="Sprint 4 planning and RACI distribution",
            agenda="Review backlog and assign tasks",
            date=self.meeting_date,
            start_time="10:00:00",
            end_time="11:30:00",
            mode=MeetingMode.VIRTUAL,
            meeting_link="https://meet.google.com/xyz-abcd-uvw",
            host=self.lead
        )
        self.meeting.attendees.add(self.lead, self.member, self.learner)

    # 1. An Authority user can create a meeting.
    def test_01_authority_user_can_create_meeting(self):
        self.client.login(username='auth_host', password=self.password)
        resp = self.client.post(reverse('meeting_create'), {
            'title': 'Authority Strategy Session',
            'description': 'Quarterly executive strategy review',
            'agenda': 'Review quarterly objectives and KPIs',
            'date': self.meeting_date,
            'start_time': '09:00',
            'end_time': '10:00',
            'mode': MeetingMode.VIRTUAL,
            'meeting_link': 'https://meet.google.com/auth-strategy',
            'attendees': [self.lead.id, self.member.id],
        })
        self.assertEqual(resp.status_code, 302)
        created_meeting = Meeting.objects.filter(title='Authority Strategy Session').first()
        self.assertIsNotNone(created_meeting)
        self.assertEqual(created_meeting.host, self.authority)
        self.assertEqual(created_meeting.mode, MeetingMode.VIRTUAL)
        self.assertEqual(created_meeting.status, MeetingStatus.SCHEDULED)

    # 2. A Core Team user can create a meeting.
    def test_02_core_team_user_can_create_meeting(self):
        self.client.login(username='lead_host', password=self.password)
        resp = self.client.post(reverse('meeting_create'), {
            'title': 'Core Team Architecture Sync',
            'description': 'Review backend API design',
            'agenda': 'Database indexing and caching strategies',
            'date': self.meeting_date,
            'start_time': '14:00',
            'end_time': '15:30',
            'mode': MeetingMode.IN_PERSON,
            'location': 'Conference Room 3A',
            'attendees': [self.member.id],
        })
        self.assertEqual(resp.status_code, 302)
        created_meeting = Meeting.objects.filter(title='Core Team Architecture Sync').first()
        self.assertIsNotNone(created_meeting)
        self.assertEqual(created_meeting.host, self.lead)
        self.assertEqual(created_meeting.mode, MeetingMode.IN_PERSON)
        self.assertEqual(created_meeting.location, 'Conference Room 3A')

    # 3. A Learner cannot create a meeting.
    def test_03_learner_cannot_create_meeting(self):
        self.client.login(username='learner_attendee', password=self.password)
        resp = self.client.post(reverse('meeting_create'), {
            'title': 'Unauthorized Learner Meeting',
            'date': self.meeting_date,
            'start_time': '11:00',
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Meeting.objects.filter(title='Unauthorized Learner Meeting').exists())

    # 4. A Member cannot create a meeting.
    def test_04_member_cannot_create_meeting(self):
        self.client.login(username='member_attendee', password=self.password)
        resp = self.client.post(reverse('meeting_create'), {
            'title': 'Unauthorized Member Meeting',
            'date': self.meeting_date,
            'start_time': '11:00',
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Meeting.objects.filter(title='Unauthorized Member Meeting').exists())

    # 5. Learners and Members cannot edit meeting details.
    def test_05_learners_and_members_cannot_edit_meeting_details(self):
        # Member attempt
        self.client.login(username='member_attendee', password=self.password)
        resp_member = self.client.post(reverse('meeting_edit', args=[self.meeting.id]), {
            'title': 'Hijacked by Member',
            'date': self.meeting_date,
            'start_time': '10:00',
        })
        self.assertEqual(resp_member.status_code, 403)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.title, "Sprint Planning Meeting")

        # Learner attempt
        self.client.login(username='learner_attendee', password=self.password)
        resp_learner = self.client.post(reverse('meeting_edit', args=[self.meeting.id]), {
            'title': 'Hijacked by Learner',
            'date': self.meeting_date,
            'start_time': '10:00',
        })
        self.assertEqual(resp_learner.status_code, 403)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.title, "Sprint Planning Meeting")

    # 6. Learners and Members cannot replace or submit the official meeting link.
    def test_06_learners_and_members_cannot_replace_meeting_link(self):
        original_link = self.meeting.meeting_link

        # Member attempt to inject external link
        self.client.login(username='member_attendee', password=self.password)
        resp = self.client.post(reverse('meeting_edit', args=[self.meeting.id]), {
            'title': self.meeting.title,
            'date': self.meeting.date,
            'start_time': self.meeting.start_time,
            'meeting_link': 'https://phishing-site.example.com/fake-meeting',
        })
        self.assertEqual(resp.status_code, 403)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.meeting_link, original_link)

        # Learner attempt
        self.client.login(username='learner_attendee', password=self.password)
        resp_l = self.client.post(reverse('meeting_edit', args=[self.meeting.id]), {
            'title': self.meeting.title,
            'date': self.meeting.date,
            'start_time': self.meeting.start_time,
            'meeting_link': 'https://learner-malicious-link.com',
        })
        self.assertEqual(resp_l.status_code, 403)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.meeting_link, original_link)

    # 7. Learners and Members cannot cancel meetings.
    def test_07_learners_and_members_cannot_cancel_meetings(self):
        self.client.login(username='member_attendee', password=self.password)
        resp_member = self.client.post(reverse('meeting_cancel', args=[self.meeting.id]))
        self.assertEqual(resp_member.status_code, 403)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.status, MeetingStatus.SCHEDULED)

        self.client.login(username='learner_attendee', password=self.password)
        resp_learner = self.client.post(reverse('meeting_cancel', args=[self.meeting.id]))
        self.assertEqual(resp_learner.status_code, 403)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.status, MeetingStatus.SCHEDULED)

    # 8. Authorized participants can access an eligible meeting's join functionality.
    def test_08_authorized_participants_can_access_join_functionality(self):
        self.client.login(username='member_attendee', password=self.password)
        resp = self.client.get(reverse('meeting_join', args=[self.meeting.id]))
        # Redirects to official meeting URL
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.meeting.meeting_link)

        # Verify accurate attendance recording: joining is distinguished from confirmed attendance
        response_record = AttendanceResponse.objects.get(meeting=self.meeting, attendee=self.member)
        self.assertTrue(response_record.joined_via_link)
        self.assertIsNotNone(response_record.joined_at)
        self.assertFalse(response_record.confirmed_attended)

    # 9. Unauthorized users cannot access restricted meeting details or links.
    def test_09_unauthorized_users_cannot_access_restricted_meeting(self):
        # other_member is not an attendee and not host/authority
        self.client.login(username='other_member', password=self.password)
        
        # Details view access blocked
        resp_detail = self.client.get(reverse('meeting_detail', args=[self.meeting.id]))
        self.assertEqual(resp_detail.status_code, 403)

        # Join link access blocked
        resp_join = self.client.get(reverse('meeting_join', args=[self.meeting.id]))
        self.assertEqual(resp_join.status_code, 403)

        # Minutes view access blocked
        resp_min = self.client.get(reverse('meeting_minutes', args=[self.meeting.id]))
        self.assertEqual(resp_min.status_code, 403)

    # 10. Invalid meeting dates, times, and URLs are rejected.
    def test_10_invalid_meeting_dates_times_and_urls_are_rejected(self):
        # 1. Invalid time: end_time earlier than start_time
        invalid_meeting = Meeting(
            title="Invalid Time Meeting",
            date=self.meeting_date,
            start_time="16:00:00",
            end_time="14:00:00", # Earlier!
            host=self.lead
        )
        with self.assertRaises(ValidationError):
            invalid_meeting.clean()

        # 2. Invalid URL: disallowed protocol (e.g. ftp:// or javascript:)
        with self.assertRaises(ValidationError):
            validate_meeting_url("ftp://ftp.example.com/meeting")

        with self.assertRaises(ValidationError):
            validate_meeting_url("javascript:alert('pwned')")

        with self.assertRaises(ValidationError):
            validate_meeting_url("not-a-valid-url")

    # 11. Only authorized users can create official minutes and assign action items.
    def test_11_only_authorized_users_create_minutes_and_action_items(self):
        # Member cannot create minutes
        self.client.login(username='member_attendee', password=self.password)
        resp_min_denied = self.client.post(reverse('meeting_minutes', args=[self.meeting.id]), {
            'discussion_summary': 'Unauthorized minutes draft',
            'decisions_made': 'None',
        })
        self.assertEqual(resp_min_denied.status_code, 403)
        self.assertFalse(MeetingMinutes.objects.filter(meeting=self.meeting).exists())

        # Member cannot assign action item to another user
        resp_item_denied = self.client.post(reverse('action_item_create', args=[self.meeting.id]), {
            'title': 'Unauthorized Item',
            'description': 'Unauthorized assign',
            'owner': self.learner.id,
        })
        self.assertEqual(resp_item_denied.status_code, 403)

        # Authorized Lead creates minutes
        self.client.login(username='lead_host', password=self.password)
        resp_min_ok = self.client.post(reverse('meeting_minutes', args=[self.meeting.id]), {
            'discussion_summary': 'Reviewed sprint deliverables and RACI assignments.',
            'decisions_made': 'Approved staging deployment for Friday.',
            'notes': 'Follow up with QA team regarding regression suites.',
        })
        self.assertEqual(resp_min_ok.status_code, 302)
        minutes = MeetingMinutes.objects.get(meeting=self.meeting)
        self.assertEqual(minutes.created_by, self.lead)
        self.assertIn("Reviewed sprint", minutes.discussion_summary)

        # Authorized Lead creates action item
        resp_item_ok = self.client.post(reverse('action_item_create', args=[self.meeting.id]), {
            'title': 'Configure CI pipeline',
            'description': 'Implement automated regression checks',
            'owner': self.member.id,
            'status': ActionItemStatus.TODO,
        })
        self.assertEqual(resp_item_ok.status_code, 302)
        self.assertTrue(ActionItem.objects.filter(meeting=self.meeting, owner=self.member).exists())

    # 12. A user cannot modify another user's tasks or assignments without permission.
    def test_12_user_cannot_modify_another_users_tasks_without_permission(self):
        action_item = ActionItem.objects.create(
            meeting=self.meeting,
            title="Setup DB migrations",
            description="Run SQLite migration check",
            owner=self.member,
            created_by=self.lead
        )

        # other_member attempts to modify member's action item -> 403 Forbidden
        self.client.login(username='other_member', password=self.password)
        resp = self.client.post(reverse('action_item_status', args=[action_item.id]), {
            'status': ActionItemStatus.DONE,
        })
        self.assertEqual(resp.status_code, 403)
        action_item.refresh_from_db()
        self.assertEqual(action_item.status, ActionItemStatus.TODO)

        # Member owner can update their OWN action item
        self.client.login(username='member_attendee', password=self.password)
        resp_owner = self.client.post(reverse('action_item_status', args=[action_item.id]), {
            'status': ActionItemStatus.IN_PROGRESS,
        })
        self.assertEqual(resp_owner.status_code, 302)
        action_item.refresh_from_db()
        self.assertEqual(action_item.status, ActionItemStatus.IN_PROGRESS)

    # 13. Unauthenticated users cannot perform protected operations.
    def test_13_unauthenticated_users_cannot_perform_protected_operations(self):
        self.client.logout()

        protected_urls = [
            (reverse('meeting_create'), 'POST'),
            (reverse('meeting_edit', args=[self.meeting.id]), 'POST'),
            (reverse('meeting_cancel', args=[self.meeting.id]), 'POST'),
            (reverse('meeting_join', args=[self.meeting.id]), 'GET'),
            (reverse('meeting_minutes', args=[self.meeting.id]), 'POST'),
            (reverse('meeting_detail', args=[self.meeting.id]), 'GET'),
        ]

        for url, method in protected_urls:
            if method == 'POST':
                resp = self.client.post(url, {})
            else:
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302, f"Failed for {url}")
            self.assertIn('/login', resp.url)

    # 14. GET requests cannot cancel or otherwise modify meetings.
    def test_14_get_requests_cannot_cancel_or_modify_meetings(self):
        self.client.login(username='lead_host', password=self.password)

        # GET request to cancel endpoint must be rejected
        resp_cancel_get = self.client.get(reverse('meeting_cancel', args=[self.meeting.id]))
        self.assertEqual(resp_cancel_get.status_code, 405) # Method Not Allowed
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.status, MeetingStatus.SCHEDULED)

        # GET request to edit endpoint renders form and does NOT modify meeting
        resp_edit_get = self.client.get(reverse('meeting_edit', args=[self.meeting.id]))
        self.assertEqual(resp_edit_get.status_code, 200)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.title, "Sprint Planning Meeting")

    # Additional existing test: absence notifications
    def test_attendance_and_absence_notification_to_host(self):
        self.client.login(username='member_attendee', password=self.password)
        absence_reason = "Attending external client workshop on security."
        resp = self.client.post(reverse('attendance_submit', args=[self.meeting.id]), {
            'status': AttendanceStatus.ABSENT,
            'absence_reason': absence_reason,
        })
        self.assertEqual(resp.status_code, 302)

        response_record = AttendanceResponse.objects.get(meeting=self.meeting, attendee=self.member)
        self.assertEqual(response_record.status, AttendanceStatus.ABSENT)
        self.assertEqual(response_record.absence_reason, absence_reason)

        notification = HostNotification.objects.filter(meeting=self.meeting, attendee=self.member).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.host, self.lead)
        self.assertEqual(notification.reason, absence_reason)

    # Additional existing test: duplicate-safe task conversion
    def test_action_item_creation_and_duplicate_safe_task_conversion(self):
        action_item = ActionItem.objects.create(
            meeting=self.meeting,
            description="Prepare automated rollback checklist",
            owner=self.member,
            due_date=self.meeting_date
        )
        self.assertFalse(action_item.is_converted)

        # Member cannot convert
        self.client.login(username='member_attendee', password=self.password)
        resp = self.client.post(reverse('action_item_convert', args=[action_item.id]))
        self.assertEqual(resp.status_code, 403)

        # Lead converts
        self.client.login(username='lead_host', password=self.password)
        resp = self.client.post(reverse('action_item_convert', args=[action_item.id]))
        self.assertEqual(resp.status_code, 302)

        action_item.refresh_from_db()
        self.assertTrue(action_item.is_converted)
        self.assertIsNotNone(action_item.converted_task)
        self.assertEqual(action_item.converted_task.assigned_to, self.member)

        initial_task_count = Task.objects.count()
        # Duplicate conversion prevented
        resp_again = self.client.post(reverse('action_item_convert', args=[action_item.id]))
        self.assertEqual(resp_again.status_code, 302)
        self.assertEqual(Task.objects.count(), initial_task_count)

