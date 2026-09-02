from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from chores_app.models import Chore, ChoreInstance, Household


class ChoreBaseFieldsTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.user = get_user_model().objects.create_user(username='alice', password='pw12345')

    def test_priority_defaults_to_medium(self):
        chore = Chore.objects.create(
            name='Wash dishes',
            recurrence_type=Chore.RECURRENCE_DEADLINE,
            created_by=self.user,
        )

        self.assertEqual(chore.priority, Chore.PRIORITY_MEDIUM)


class ChoreNextDueDateTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.user = get_user_model().objects.create_user(username='alice', password='pw12345')

    def test_interval_recurrence_adds_interval_days(self):
        chore = Chore.objects.create(
            name='Water plants',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=5,
            created_by=self.user,
        )
        from_date = date(2026, 9, 2)

        self.assertEqual(chore.next_due_date(from_date), date(2026, 9, 7))

    def test_weekdays_recurrence_returns_next_match_same_week(self):
        chore = Chore.objects.create(
            name='Take out trash',
            recurrence_type=Chore.RECURRENCE_WEEKDAYS,
            weekdays='1,3',
            created_by=self.user,
        )
        from_date = date(2026, 9, 1)

        self.assertEqual(chore.next_due_date(from_date), date(2026, 9, 2))

    def test_weekdays_recurrence_wraps_to_next_week(self):
        chore = Chore.objects.create(
            name='Take out trash',
            recurrence_type=Chore.RECURRENCE_WEEKDAYS,
            weekdays='1,3',
            created_by=self.user,
        )
        from_date = date(2026, 9, 3)

        self.assertEqual(from_date.isoweekday(), 4)
        self.assertEqual(chore.next_due_date(from_date), date(2026, 9, 7))

    def test_deadline_recurrence_returns_from_date_unchanged(self):
        chore = Chore.objects.create(
            name='Renew passport',
            recurrence_type=Chore.RECURRENCE_DEADLINE,
            created_by=self.user,
        )
        from_date = date(2026, 9, 2)

        self.assertEqual(chore.next_due_date(from_date), from_date)


class ChoreCreateNextInstanceTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.user = get_user_model().objects.create_user(username='alice', password='pw12345')

    def test_creates_instance_with_computed_due_date(self):
        chore = Chore.objects.create(
            name='Water plants',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=5,
            created_by=self.user,
        )
        from_date = date(2026, 9, 2)

        instance = chore.create_next_instance(from_date=from_date)

        self.assertEqual(instance.due_date, chore.next_due_date(from_date))

    def test_instance_status_defaults_to_pending(self):
        chore = Chore.objects.create(
            name='Water plants',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=5,
            created_by=self.user,
        )

        instance = chore.create_next_instance(from_date=date(2026, 9, 2))

        self.assertEqual(instance.status, ChoreInstance.STATUS_PENDING)

    def test_omitted_from_date_defaults_to_today(self):
        chore = Chore.objects.create(
            name='Water plants',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=5,
            created_by=self.user,
        )

        instance = chore.create_next_instance()

        self.assertEqual(instance.due_date, chore.next_due_date(date.today()))
