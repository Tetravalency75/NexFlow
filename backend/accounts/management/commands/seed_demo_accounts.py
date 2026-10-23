from django.core.management.base import BaseCommand
from accounts.models import User, Role

class Command(BaseCommand):
    help = 'Seeds or updates the four standardized demo accounts representing all four NEXFlow roles.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='NexFlow2026!',
            help='Initial password for demo accounts (defaults to NexFlow2026!)'
        )

    def handle(self, *args, **options):
        password = options['password']

        demo_users_data = [
            {
                'username': 'alexa.authority',
                'email': 'alexa.authority@nexflow.io',
                'first_name': 'Alexa',
                'last_name': 'Vance',
                'role': Role.AUTHORITY,
                'job_title': 'Executive Authority & Director',
                'avatar': 'images/avatar-3.svg',
                'department': 'Executive & Governance',
                'is_staff': True,
            },
            {
                'username': 'alex.morgan',
                'email': 'alex.morgan@nexflow.io',
                'first_name': 'Alex',
                'last_name': 'Morgan',
                'role': Role.LEAD,
                'job_title': 'Team Lead & Solutions Architect',
                'avatar': 'images/avatar-1.svg',
                'department': 'Core Platform',
                'is_staff': False,
            },
            {
                'username': 'sarah.chen',
                'email': 'sarah.chen@nexflow.io',
                'first_name': 'Sarah',
                'last_name': 'Chen',
                'role': Role.MEMBER,
                'job_title': 'Senior Fullstack Engineer',
                'avatar': 'images/avatar-2.svg',
                'department': 'Web Experience',
                'is_staff': False,
            },
            {
                'username': 'leo.learner',
                'email': 'leo.learner@nexflow.io',
                'first_name': 'Leo',
                'last_name': 'Brooks',
                'role': Role.LEARNER,
                'job_title': 'Associate Developer & Learner',
                'avatar': 'images/avatar-4.svg',
                'department': 'Frontend Foundations',
                'is_staff': False,
            },
        ]

        created_count = 0
        updated_count = 0

        for user_data in demo_users_data:
            username = user_data['username']
            email = user_data['email']

            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.filter(email=email).first()

            if user:
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.role = user_data['role']
                user.job_title = user_data['job_title']
                user.avatar = user_data['avatar']
                user.department = user_data['department']
                user.is_staff = user_data['is_staff']
                user.set_password(password)
                user.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Updated demo user '{username}' -> Role: {user.role}"))
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    job_title=user_data['job_title'],
                    avatar=user_data['avatar'],
                    department=user_data['department'],
                    is_staff=user_data['is_staff'],
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created demo user '{username}' -> Role: {user.role}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nFinished seeding demo accounts. Created: {created_count}, Updated: {updated_count}."
            f"\nStandard password set to: {password}"
        ))
