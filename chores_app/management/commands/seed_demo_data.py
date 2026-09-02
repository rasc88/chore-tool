from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from chores_app.models import Chore, ChoreInstance, Household, Profile

HOUSEHOLD_NAME = 'The Demo Household'
DEMO_PASSWORD = 'demo1234'

DEMO_USERS = [
    {'username': 'alice', 'first_name': 'Alice', 'is_admin': True},
    {'username': 'bob', 'first_name': 'Bob', 'is_admin': True},
    {'username': 'charlie', 'first_name': 'Charlie', 'is_admin': False},
    {'username': 'dana', 'first_name': 'Dana', 'is_admin': False},
    {'username': 'erin', 'first_name': 'Erin', 'is_admin': False},
]

CHORE_NAMES = [
    'Wash dishes',
    'Take out trash',
    'Deep clean bathroom',
    'Vacuum living room',
    'Mow the lawn',
    'Clean kitchen',
]


class Command(BaseCommand):
    help = 'Seeds a demo household with users, chores, and chore instances for manual testing.'

    def handle(self, *args, **options):
        if Household.objects.filter(name=HOUSEHOLD_NAME).exists():
            self.stdout.write(f'"{HOUSEHOLD_NAME}" already exists, clearing it before reseeding.')
            self._clear_existing()

        with transaction.atomic():
            household = Household.objects.create(name=HOUSEHOLD_NAME)
            users = self._create_users(household)
            chores = self._create_chores(users)
            instance_count = self._create_instances(chores, users)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded household "{household.name}" with {len(users)} users, '
            f'{len(chores)} chores, and {instance_count} chore instances.'
        ))
        self.stdout.write(f'Demo login password for every user: {DEMO_PASSWORD}')
        self.stdout.write('Usernames: ' + ', '.join(sorted(users.keys())))

    def _clear_existing(self):
        # Chores must go first: created_by is PROTECT, so the demo users
        # can't be deleted while they still own chores.
        Chore.objects.filter(name__in=CHORE_NAMES).delete()
        get_user_model().objects.filter(username__in=[u['username'] for u in DEMO_USERS]).delete()
        Household.objects.filter(name=HOUSEHOLD_NAME).delete()

    def _create_users(self, household):
        user_model = get_user_model()
        users = {}
        for spec in DEMO_USERS:
            user = user_model.objects.create_user(
                username=spec['username'],
                password=DEMO_PASSWORD,
                first_name=spec['first_name'],
            )
            Profile.objects.create(user=user, household=household, is_admin=spec['is_admin'])
            users[spec['username']] = user
        return users

    def _create_chores(self, users):
        admin = users['alice']
        chores = {}

        chores['dishes'] = Chore.objects.create(
            name='Wash dishes',
            description='Wash and put away dishes after dinner.',
            priority=Chore.PRIORITY_MEDIUM,
            recurrence_type=Chore.RECURRENCE_WEEKDAYS,
            weekdays='1,3,5',
            assignment_type=Chore.ASSIGNMENT_ROTATING,
            created_by=admin,
        )
        chores['dishes'].rotation_members.set(
            [users['alice'], users['bob'], users['charlie'], users['dana']]
        )

        chores['trash'] = Chore.objects.create(
            name='Take out trash',
            description='Bins go out for collection day.',
            priority=Chore.PRIORITY_LOW,
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=7,
            assignment_type=Chore.ASSIGNMENT_FIXED,
            fixed_assignee=users['charlie'],
            created_by=admin,
        )

        chores['bathroom'] = Chore.objects.create(
            name='Deep clean bathroom',
            description='Scrub tub, tile, and floor.',
            priority=Chore.PRIORITY_HIGH,
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=14,
            assignment_type=Chore.ASSIGNMENT_POOL,
            created_by=admin,
        )

        chores['vacuum'] = Chore.objects.create(
            name='Vacuum living room',
            description='Vacuum carpets and rugs.',
            priority=Chore.PRIORITY_MEDIUM,
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=3,
            assignment_type=Chore.ASSIGNMENT_ROTATING,
            created_by=admin,
        )
        chores['vacuum'].rotation_members.set([users['dana'], users['erin']])

        chores['lawn'] = Chore.objects.create(
            name='Mow the lawn',
            description='Mow front and back yard.',
            priority=Chore.PRIORITY_MEDIUM,
            recurrence_type=Chore.RECURRENCE_DEADLINE,
            assignment_type=Chore.ASSIGNMENT_FIXED,
            fixed_assignee=users['bob'],
            created_by=users['bob'],
        )

        chores['kitchen'] = Chore.objects.create(
            name='Clean kitchen',
            description='Wipe counters, stove, and floor.',
            priority=Chore.PRIORITY_HIGH,
            recurrence_type=Chore.RECURRENCE_WEEKDAYS,
            weekdays='2,4',
            assignment_type=Chore.ASSIGNMENT_POOL,
            created_by=admin,
        )

        return chores

    def _create_instances(self, chores, users):
        today = date.today()
        now = timezone.now()
        count = 0

        def make(chore, due_date, status=ChoreInstance.STATUS_PENDING, assigned_to=None,
                 completed_by=None, completed_at=None):
            nonlocal count
            ChoreInstance.objects.create(
                chore=chore,
                due_date=due_date,
                status=status,
                assigned_to=assigned_to,
                completed_by=completed_by,
                completed_at=completed_at,
            )
            count += 1

        make(chores['dishes'], today, assigned_to=users['alice'])
        make(chores['dishes'], today - timedelta(days=3), status=ChoreInstance.STATUS_DONE,
             assigned_to=users['charlie'], completed_by=users['charlie'],
             completed_at=now - timedelta(days=3))

        make(chores['trash'], today, assigned_to=users['charlie'])
        make(chores['trash'], today - timedelta(days=2), status=ChoreInstance.STATUS_DONE,
             assigned_to=users['charlie'], completed_by=users['charlie'],
             completed_at=now - timedelta(days=2))

        make(chores['bathroom'], today)
        make(chores['bathroom'], today - timedelta(days=5))

        make(chores['vacuum'], today, assigned_to=users['dana'])
        make(chores['vacuum'], today - timedelta(days=2), assigned_to=users['erin'])

        make(chores['lawn'], today + timedelta(days=3), assigned_to=users['bob'])
        make(chores['lawn'], today - timedelta(days=10), status=ChoreInstance.STATUS_DONE,
             assigned_to=users['bob'], completed_by=users['bob'],
             completed_at=now - timedelta(days=10))

        make(chores['kitchen'], today)
        make(chores['kitchen'], today - timedelta(days=1), status=ChoreInstance.STATUS_DONE,
             assigned_to=users['erin'], completed_by=users['erin'],
             completed_at=now - timedelta(days=1))

        return count
