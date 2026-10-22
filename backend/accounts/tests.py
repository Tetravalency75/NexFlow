from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, Role

class RoleAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'TestPassword123!'
        self.authority = User.objects.create_user(
            username='authority_user',
            email='auth@nexflow.io',
            password=self.password,
            role=Role.AUTHORITY
        )
        self.lead = User.objects.create_user(
            username='lead_user',
            email='lead@nexflow.io',
            password=self.password,
            role=Role.LEAD
        )
        self.member = User.objects.create_user(
            username='member_user',
            email='member@nexflow.io',
            password=self.password,
            role=Role.MEMBER
        )
        self.learner = User.objects.create_user(
            username='learner_user',
            email='learner@nexflow.io',
            password=self.password,
            role=Role.LEARNER
        )

    def test_all_four_roles_can_login(self):
        roles = [
            (self.authority, Role.AUTHORITY),
            (self.lead, Role.LEAD),
            (self.member, Role.MEMBER),
            (self.learner, Role.LEARNER),
        ]
        for user, expected_role in roles:
            self.client.logout()
            response = self.client.post(reverse('login'), {
                'username_or_email': user.email,
                'password': self.password,
            })
            self.assertEqual(response.status_code, 302, f"Failed login for {user.username}")
            self.assertEqual(user.role, expected_role)

    def test_role_properties(self):
        self.assertTrue(self.authority.is_authority)
        self.assertTrue(self.authority.can_assign_tasks)
        self.assertTrue(self.authority.can_verify_proof)

        self.assertTrue(self.lead.is_lead)
        self.assertTrue(self.lead.can_assign_tasks)
        self.assertFalse(self.lead.can_verify_proof)

        self.assertTrue(self.member.is_member)
        self.assertFalse(self.member.can_assign_tasks)
        self.assertFalse(self.member.can_verify_proof)

        self.assertTrue(self.learner.is_learner)
        self.assertFalse(self.learner.can_assign_tasks)
        self.assertFalse(self.learner.can_verify_proof)
