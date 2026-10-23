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

    def test_invalid_password(self):
        response = self.client.post(reverse('login'), {
            'username_or_email': self.authority.email,
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, "Invalid credentials. Please verify your email/username and password.")
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_unknown_email(self):
        response = self.client.post(reverse('login'), {
            'username_or_email': 'nonexistent@nexflow.io',
            'password': 'SomePassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, "Invalid credentials. Please verify your email/username and password.")
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_role_based_dashboard_redirects(self):
        role_targets = [
            (self.authority, reverse('authority_dashboard')),
            (self.lead, reverse('lead_dashboard')),
            (self.member, reverse('member_dashboard')),
            (self.learner, reverse('learner_dashboard')),
        ]
        for user, expected_target in role_targets:
            self.client.logout()
            # 1. Login user
            login_resp = self.client.post(reverse('login'), {
                'username_or_email': user.email,
                'password': self.password,
            }, follow=False)
            self.assertEqual(login_resp.status_code, 302)
            self.assertEqual(login_resp.url, reverse('dashboard'))

            # 2. Access /dashboard/ central router
            dash_resp = self.client.get(reverse('dashboard'), follow=False)
            self.assertEqual(dash_resp.status_code, 302)
            self.assertEqual(dash_resp.url, expected_target)

            # 3. Following redirect loads the dashboard successfully
            page_resp = self.client.get(expected_target)
            self.assertEqual(page_resp.status_code, 200)

    def test_unauthorized_access_to_authority_dashboard(self):
        # Members and Learners must NOT access authority dashboard
        unauthorized_users = [self.lead, self.member, self.learner]
        for user in unauthorized_users:
            self.client.force_login(user)
            resp = self.client.get(reverse('authority_dashboard'))
            self.assertEqual(resp.status_code, 403, f"{user.role} was not forbidden from Authority dashboard")

        # Unauthenticated users are redirected to login
        self.client.logout()
        resp = self.client.get(reverse('authority_dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(reverse('login') in resp.url)

    def test_tampered_role_in_post_is_ignored(self):
        # Attempting to send a role parameter during login does not grant authority
        self.client.logout()
        resp = self.client.post(reverse('login'), {
            'username_or_email': self.member.email,
            'password': self.password,
            'role': 'Authority',
            'is_authority': 'true'
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Verify authenticated user is still Member and cannot reach authority dashboard
        auth_resp = self.client.get(reverse('authority_dashboard'))
        self.assertEqual(auth_resp.status_code, 403)

