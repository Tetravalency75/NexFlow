from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, Role
from tasks.models import Task
from meetings.models import Meeting, AttendanceResponse, AttendanceStatus, HostNotification, ActionItem

class MeetingAndAttendanceTests(TestCase):
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
        self.learner = User.objects.create_user(
            username='learner_attendee', email='learner_att@test.com', password=self.password, role=Role.LEARNER
        )

        # Create a sample meeting hosted by the Lead
        self.meeting_date = timezone.now().date() + timedelta(days=2)
        self.meeting = Meeting.objects.create(
            title="Sprint Planning Meeting",
            agenda="Review backlog and assign tasks",
            date=self.meeting_date,
            start_time="10:00:00",
            meeting_link="https://meet.google.com/xyz-abcd-uvw",
            host=self.lead
        )
        self.meeting.attendees.add(self.lead, self.member, self.learner)

    def test_meeting_creation_permissions(self):
        # 1. Lead can create a meeting
        self.client.login(username='lead_host', password=self.password)
        resp = self.client.post(reverse('meeting_create'), {
            'title': 'Lead Sync Meeting',
            'agenda': 'Sync on deliverables',
            'date': self.meeting_date,
            'start_time': '14:00',
            'meeting_link': 'https://teams.microsoft.com/l/meetup-join/12345',
            'attendees': [self.member.id],
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Meeting.objects.filter(title='Lead Sync Meeting').exists())

        # 2. Authority can create a meeting
        self.client.login(username='auth_host', password=self.password)
        resp = self.client.post(reverse('meeting_create'), {
            'title': 'All-Hands Architecture Review',
            'agenda': 'Quarterly architecture review',
            'date': self.meeting_date,
            'start_time': '16:00',
            'meeting_link': 'https://meet.google.com/auth-review',
            'attendees': [self.lead.id, self.member.id],
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Meeting.objects.filter(title='All-Hands Architecture Review').exists())

        # 3. Member CANNOT create a meeting (403 Forbidden)
        self.client.login(username='member_attendee', password=self.password)
        resp = self.client.post(reverse('meeting_create'), {
            'title': 'Unauthorized Member Meeting',
            'date': self.meeting_date,
            'start_time': '11:00',
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Meeting.objects.filter(title='Unauthorized Member Meeting').exists())

        # 4. Learner CANNOT create a meeting (403 Forbidden)
        self.client.login(username='learner_attendee', password=self.password)
        resp = self.client.post(reverse('meeting_create'), {
            'title': 'Unauthorized Learner Meeting',
            'date': self.meeting_date,
            'start_time': '11:00',
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Meeting.objects.filter(title='Unauthorized Learner Meeting').exists())

    def test_attendance_and_absence_notification_to_host(self):
        # 1. Member submits absence with reason
        self.client.login(username='member_attendee', password=self.password)
        absence_reason = "Attending external client workshop on security."
        resp = self.client.post(reverse('attendance_submit', args=[self.meeting.id]), {
            'status': AttendanceStatus.ABSENT,
            'absence_reason': absence_reason,
        })
        self.assertEqual(resp.status_code, 302)

        # Verify AttendanceResponse record
        response_record = AttendanceResponse.objects.get(meeting=self.meeting, attendee=self.member)
        self.assertEqual(response_record.status, AttendanceStatus.ABSENT)
        self.assertEqual(response_record.absence_reason, absence_reason)

        # Verify HostNotification was generated for meeting host (lead)
        notification = HostNotification.objects.filter(meeting=self.meeting, attendee=self.member).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.host, self.lead)
        self.assertEqual(notification.reason, absence_reason)

        # 2. Learner marks attending
        self.client.login(username='learner_attendee', password=self.password)
        resp = self.client.post(reverse('attendance_submit', args=[self.meeting.id]), {
            'status': AttendanceStatus.ATTENDING,
            'absence_reason': '',
        })
        self.assertEqual(resp.status_code, 302)

        response_learner = AttendanceResponse.objects.get(meeting=self.meeting, attendee=self.learner)
        self.assertEqual(response_learner.status, AttendanceStatus.ATTENDING)

    def test_action_item_creation_and_duplicate_safe_task_conversion(self):
        # 1. Host creates an action item
        action_item = ActionItem.objects.create(
            meeting=self.meeting,
            description="Prepare automated rollback checklist",
            owner=self.member,
            due_date=self.meeting_date
        )
        self.assertFalse(action_item.is_converted)

        # 2. Member tries to convert action item into task -> 403 Forbidden (Only Auth/Lead can assign)
        self.client.login(username='member_attendee', password=self.password)
        resp = self.client.post(reverse('action_item_convert', args=[action_item.id]))
        self.assertEqual(resp.status_code, 403)
        action_item.refresh_from_db()
        self.assertFalse(action_item.is_converted)

        # 3. Lead converts action item into task -> Success
        self.client.login(username='lead_host', password=self.password)
        resp = self.client.post(reverse('action_item_convert', args=[action_item.id]))
        self.assertEqual(resp.status_code, 302)

        action_item.refresh_from_db()
        self.assertTrue(action_item.is_converted)
        self.assertIsNotNone(action_item.converted_task)
        self.assertEqual(action_item.converted_task.assigned_to, self.member)
        self.assertIn("Prepare automated rollback checklist", action_item.converted_task.title)

        initial_task_count = Task.objects.count()

        # 4. Attempt to convert AGAIN -> Idempotent prevention of duplicates!
        resp_again = self.client.post(reverse('action_item_convert', args=[action_item.id]))
        self.assertEqual(resp_again.status_code, 302)
        # Ensure no second task was created
        self.assertEqual(Task.objects.count(), initial_task_count)
