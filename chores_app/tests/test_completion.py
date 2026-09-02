from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from chores_app.models import Chore, ChoreInstance, Household


class ChoreInstanceMarkDoneTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.user = get_user_model().objects.create_user(username='alice', password='pw12345')
        self.other_user = get_user_model().objects.create_user(username='bob', password='pw12345')

    def _create_chore(self, recurrence_type, **kwargs):
        return Chore.objects.create(
            name='Wash dishes',
            recurrence_type=recurrence_type,
            created_by=self.user,
            **kwargs,
        )

    def test_mark_done_sets_status_and_completed_by(self):
        chore = self._create_chore(Chore.RECURRENCE_INTERVAL, interval_days=7)
        instance = ChoreInstance.objects.create(chore=chore, due_date=timezone.now().date())

        instance.mark_done(self.user)

        self.assertEqual(instance.status, ChoreInstance.STATUS_DONE)
        self.assertEqual(instance.completed_by, self.user)

    def test_mark_done_sets_completed_at_to_recent_timestamp(self):
        chore = self._create_chore(Chore.RECURRENCE_INTERVAL, interval_days=7)
        instance = ChoreInstance.objects.create(chore=chore, due_date=timezone.now().date())

        instance.mark_done(self.user)

        self.assertIsNotNone(instance.completed_at)
        self.assertLessEqual(abs((timezone.now() - instance.completed_at).total_seconds()), 5)

    def test_mark_done_on_deadline_chore_creates_one_new_instance(self):
        chore = self._create_chore(Chore.RECURRENCE_DEADLINE)
        instance = ChoreInstance.objects.create(chore=chore, due_date=timezone.now().date())

        before_count = chore.instances.count()
        instance.mark_done(self.user)

        self.assertEqual(chore.instances.count(), before_count + 1)

    def test_mark_done_on_interval_chore_does_not_create_new_instance(self):
        chore = self._create_chore(Chore.RECURRENCE_INTERVAL, interval_days=7)
        instance = ChoreInstance.objects.create(chore=chore, due_date=timezone.now().date())

        before_count = chore.instances.count()
        instance.mark_done(self.user)

        self.assertEqual(chore.instances.count(), before_count)

    def test_mark_done_on_weekdays_chore_does_not_create_new_instance(self):
        chore = self._create_chore(Chore.RECURRENCE_WEEKDAYS, weekdays='1,3,5')
        instance = ChoreInstance.objects.create(chore=chore, due_date=timezone.now().date())

        before_count = chore.instances.count()
        instance.mark_done(self.user)

        self.assertEqual(chore.instances.count(), before_count)

    def test_mark_done_on_already_done_instance_overwrites_fields(self):
        chore = self._create_chore(Chore.RECURRENCE_INTERVAL, interval_days=7)
        instance = ChoreInstance.objects.create(chore=chore, due_date=timezone.now().date())
        instance.mark_done(self.user)
        first_completed_at = instance.completed_at

        instance.mark_done(self.other_user)

        self.assertEqual(instance.status, ChoreInstance.STATUS_DONE)
        self.assertEqual(instance.completed_by, self.other_user)
        self.assertGreaterEqual(instance.completed_at, first_completed_at)


class ChoreInstanceCompletedQuerySetTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.user = get_user_model().objects.create_user(username='alice', password='pw12345')
        self.chore = Chore.objects.create(
            name='Wash dishes',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=7,
            created_by=self.user,
        )

    def test_completed_excludes_pending_and_overdue_instances(self):
        today = timezone.now().date()
        done_instance = ChoreInstance.objects.create(chore=self.chore, due_date=today)
        done_instance.mark_done(self.user)
        ChoreInstance.objects.create(chore=self.chore, due_date=today, status=ChoreInstance.STATUS_PENDING)
        ChoreInstance.objects.create(chore=self.chore, due_date=today, status=ChoreInstance.STATUS_OVERDUE)

        result = ChoreInstance.objects.completed()

        self.assertEqual(list(result), [done_instance])

    def test_completed_orders_by_completed_at_descending(self):
        today = timezone.now().date()
        now = timezone.now()
        oldest = ChoreInstance.objects.create(
            chore=self.chore, due_date=today, status=ChoreInstance.STATUS_DONE,
            completed_by=self.user, completed_at=now - timedelta(days=2),
        )
        newest = ChoreInstance.objects.create(
            chore=self.chore, due_date=today, status=ChoreInstance.STATUS_DONE,
            completed_by=self.user, completed_at=now,
        )
        middle = ChoreInstance.objects.create(
            chore=self.chore, due_date=today, status=ChoreInstance.STATUS_DONE,
            completed_by=self.user, completed_at=now - timedelta(days=1),
        )

        result = list(ChoreInstance.objects.completed())

        self.assertEqual(result, [newest, middle, oldest])
