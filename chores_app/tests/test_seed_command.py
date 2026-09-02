from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from chores_app.models import Chore, ChoreInstance, Household, Profile


class SeedDemoDataTests(TestCase):
    def test_creates_expected_counts(self):
        call_command('seed_demo_data', stdout=StringIO())

        self.assertEqual(Household.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 5)
        self.assertEqual(Chore.objects.count(), 6)
        self.assertEqual(ChoreInstance.objects.count(), 12)

    def test_creates_admin_users(self):
        call_command('seed_demo_data', stdout=StringIO())

        admin_usernames = set(
            Profile.objects.filter(is_admin=True).values_list('user__username', flat=True)
        )

        self.assertEqual(admin_usernames, {'alice', 'bob'})

    def test_prints_demo_password(self):
        out = StringIO()

        call_command('seed_demo_data', stdout=out)

        self.assertIn('demo1234', out.getvalue())

    def test_running_twice_does_not_duplicate_data(self):
        call_command('seed_demo_data', stdout=StringIO())

        household_count = Household.objects.count()
        profile_count = Profile.objects.count()
        chore_count = Chore.objects.count()
        instance_count = ChoreInstance.objects.count()

        call_command('seed_demo_data', stdout=StringIO())

        self.assertEqual(Household.objects.count(), household_count)
        self.assertEqual(Profile.objects.count(), profile_count)
        self.assertEqual(Chore.objects.count(), chore_count)
        self.assertEqual(ChoreInstance.objects.count(), instance_count)
