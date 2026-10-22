from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User, Role
from tasks.models import Task, TaskStatus, TaskPriority, RaciRole, ProofOfWork, ProofStatus

class TaskAndProofPermissionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'Pass12345!'
        self.authority = User.objects.create_user(
            username='auth_test', email='auth@test.com', password=self.password, role=Role.AUTHORITY
        )
        self.lead = User.objects.create_user(
            username='lead_test', email='lead@test.com', password=self.password, role=Role.LEAD
        )
        self.member = User.objects.create_user(
            username='member_test', email='member@test.com', password=self.password, role=Role.MEMBER
        )
        self.learner = User.objects.create_user(
            username='learner_test', email='learner@test.com', password=self.password, role=Role.LEARNER
        )

    def test_task_assignment_permission_restricted_to_authority_and_lead(self):
        # 1. Lead can assign tasks
        self.client.login(username='lead_test', password=self.password)
        resp = self.client.post(reverse('task_create'), {
            'title': 'Lead Created Task',
            'assigned_to': self.member.id,
            'priority': TaskPriority.HIGH,
            'raci_role': RaciRole.RESPONSIBLE,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Task.objects.filter(title='Lead Created Task').exists())

        # 2. Authority can assign tasks
        self.client.login(username='auth_test', password=self.password)
        resp = self.client.post(reverse('task_create'), {
            'title': 'Authority Created Task',
            'assigned_to': self.learner.id,
            'priority': TaskPriority.MEDIUM,
            'raci_role': RaciRole.RESPONSIBLE,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Task.objects.filter(title='Authority Created Task').exists())

        # 3. Member CANNOT assign tasks (Returns 403 Forbidden)
        self.client.login(username='member_test', password=self.password)
        resp = self.client.post(reverse('task_create'), {
            'title': 'Unauthorized Member Task',
            'assigned_to': self.learner.id,
            'priority': TaskPriority.LOW,
            'raci_role': RaciRole.RESPONSIBLE,
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Task.objects.filter(title='Unauthorized Member Task').exists())

        # 4. Learner CANNOT assign tasks (Returns 403 Forbidden)
        self.client.login(username='learner_test', password=self.password)
        resp = self.client.post(reverse('task_create'), {
            'title': 'Unauthorized Learner Task',
            'assigned_to': self.member.id,
            'priority': TaskPriority.LOW,
            'raci_role': RaciRole.RESPONSIBLE,
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Task.objects.filter(title='Unauthorized Learner Task').exists())

    def test_proof_submission_and_authority_verification_rules(self):
        # Create a task for Member
        task = Task.objects.create(
            title="API Security Module",
            created_by=self.lead,
            assigned_to=self.member,
            status=TaskStatus.IN_PROGRESS
        )

        # 1. Member submits proof of work
        self.client.login(username='member_test', password=self.password)
        resp = self.client.post(reverse('proof_submit'), {
            'task': task.id,
            'description': 'Implemented JWT token rotation and authentication tests.',
            'proof_url': 'https://github.com/nexflow/security-pr/10',
        })
        self.assertEqual(resp.status_code, 302)
        proof = ProofOfWork.objects.get(task=task)
        self.assertEqual(proof.status, ProofStatus.PENDING)

        # 2. Lead CANNOT verify proof (Only Authorities can verify proof)
        self.client.login(username='lead_test', password=self.password)
        resp = self.client.post(reverse('proof_verify', args=[proof.id]), {
            'decision': 'APPROVE',
            'feedback': 'Looks good from lead perspective.'
        })
        self.assertEqual(resp.status_code, 403)
        proof.refresh_from_db()
        self.assertEqual(proof.status, ProofStatus.PENDING)

        # 3. Authority verifies and approves proof
        self.client.login(username='auth_test', password=self.password)
        resp = self.client.post(reverse('proof_verify', args=[proof.id]), {
            'decision': 'APPROVE',
            'feedback': 'Verified and approved with high quality code.'
        })
        self.assertEqual(resp.status_code, 302)
        proof.refresh_from_db()
        self.assertEqual(proof.status, ProofStatus.APPROVED)
        self.assertEqual(proof.points_awarded, 10)
        self.assertEqual(proof.reviewed_by, self.authority)

        # Verify submitter received 10 points
        self.member.refresh_from_db()
        self.assertEqual(self.member.points, 10)

    def test_prevent_authority_self_approval(self):
        # Authority submits proof for their own task
        auth_task = Task.objects.create(
            title="Strategic Architecture Blueprint",
            created_by=self.authority,
            assigned_to=self.authority,
            status=TaskStatus.DONE
        )
        auth_proof = ProofOfWork.objects.create(
            task=auth_task,
            user=self.authority,
            description="Completed architecture diagrams."
        )

        # Authority tries to approve their OWN proof -> REJECTED with 403 Conflict of Interest!
        self.client.login(username='auth_test', password=self.password)
        resp = self.client.post(reverse('proof_verify', args=[auth_proof.id]), {
            'decision': 'APPROVE',
            'feedback': 'Approving my own work.'
        })
        self.assertEqual(resp.status_code, 403)
        auth_proof.refresh_from_db()
        self.assertEqual(auth_proof.status, ProofStatus.PENDING)
