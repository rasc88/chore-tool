from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from chores_app.models import Chore, ChoreInstance, Household, Profile


class ChoreConflictTestCase(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Test Household')
        User = get_user_model()
        self.alice = User.objects.create_user(username='alice', password='pass1234')
        self.bob = User.objects.create_user(username='bob', password='pass1234')
        Profile.objects.create(user=self.alice, household=self.household, is_admin=True)
        Profile.objects.create(user=self.bob, household=self.household)
        self.chore = Chore.objects.create(
            name='Dishes',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=1,
            created_by=self.alice,
        )
        self.today = timezone.now().date()

    def make_instance(self, due_date, status, assigned_to=None):
        return ChoreInstance.objects.create(
            chore=self.chore,
            due_date=due_date,
            status=status,
            assigned_to=assigned_to,
        )


class IsOverdueTests(ChoreConflictTestCase):
    def test_pending_past_due_is_overdue(self):
        instance = self.make_instance(self.today - timedelta(days=1), ChoreInstance.STATUS_PENDING)
        self.assertTrue(instance.is_overdue)

    def test_pending_due_today_is_not_overdue(self):
        instance = self.make_instance(self.today, ChoreInstance.STATUS_PENDING)
        self.assertFalse(instance.is_overdue)

    def test_pending_future_due_is_not_overdue(self):
        instance = self.make_instance(self.today + timedelta(days=1), ChoreInstance.STATUS_PENDING)
        self.assertFalse(instance.is_overdue)

    def test_done_past_due_is_not_overdue(self):
        instance = self.make_instance(self.today - timedelta(days=1), ChoreInstance.STATUS_DONE)
        self.assertFalse(instance.is_overdue)


class IsUnclaimedTests(ChoreConflictTestCase):
    def test_pending_unassigned_is_unclaimed(self):
        instance = self.make_instance(self.today, ChoreInstance.STATUS_PENDING)
        self.assertTrue(instance.is_unclaimed)

    def test_pending_assigned_is_not_unclaimed(self):
        instance = self.make_instance(self.today, ChoreInstance.STATUS_PENDING, assigned_to=self.alice)
        self.assertFalse(instance.is_unclaimed)

    def test_done_unassigned_is_not_unclaimed(self):
        instance = self.make_instance(self.today, ChoreInstance.STATUS_DONE)
        self.assertFalse(instance.is_unclaimed)


class ChoreInstanceQuerySetTests(ChoreConflictTestCase):
    def setUp(self):
        super().setUp()
        self.overdue_unclaimed = self.make_instance(
            self.today - timedelta(days=1), ChoreInstance.STATUS_PENDING
        )
        self.overdue_assigned = self.make_instance(
            self.today - timedelta(days=1), ChoreInstance.STATUS_PENDING, assigned_to=self.alice
        )
        self.unclaimed_not_overdue = self.make_instance(
            self.today + timedelta(days=1), ChoreInstance.STATUS_PENDING
        )
        self.done_past = self.make_instance(
            self.today - timedelta(days=1), ChoreInstance.STATUS_DONE
        )
        self.future_assigned = self.make_instance(
            self.today + timedelta(days=1), ChoreInstance.STATUS_PENDING, assigned_to=self.bob
        )

    def test_overdue_returns_pending_past_due_only(self):
        expected = sorted([self.overdue_unclaimed.id, self.overdue_assigned.id])
        actual = sorted(ChoreInstance.objects.overdue().values_list('id', flat=True))
        self.assertEqual(actual, expected)

    def test_unclaimed_returns_pending_unassigned_only(self):
        expected = sorted([self.overdue_unclaimed.id, self.unclaimed_not_overdue.id])
        actual = sorted(ChoreInstance.objects.unclaimed().values_list('id', flat=True))
        self.assertEqual(actual, expected)

    def test_flagged_is_union_of_overdue_and_unclaimed_without_duplicates(self):
        expected = sorted([
            self.overdue_unclaimed.id,
            self.overdue_assigned.id,
            self.unclaimed_not_overdue.id,
        ])
        actual = sorted(ChoreInstance.objects.flagged().values_list('id', flat=True))
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), len(set(actual)))


class EscalatedBoundaryTests(ChoreConflictTestCase):
    def setUp(self):
        super().setUp()
        # escalated() filters strictly (`__lt`), so a due date exactly `days`
        # ago sits right on the boundary and must not qualify.
        self.due_exactly_3_days_ago = self.make_instance(
            self.today - timedelta(days=3), ChoreInstance.STATUS_PENDING, assigned_to=self.alice
        )
        self.due_4_days_ago = self.make_instance(
            self.today - timedelta(days=4), ChoreInstance.STATUS_PENDING, assigned_to=self.alice
        )

    def test_due_exactly_3_days_ago_is_not_escalated(self):
        ids = list(ChoreInstance.objects.escalated(days=3).values_list('id', flat=True))
        self.assertNotIn(self.due_exactly_3_days_ago.id, ids)

    def test_due_4_days_ago_is_escalated(self):
        ids = list(ChoreInstance.objects.escalated(days=3).values_list('id', flat=True))
        self.assertIn(self.due_4_days_ago.id, ids)


class ReassignTests(ChoreConflictTestCase):
    def test_reassign_sets_and_persists_assigned_to(self):
        instance = self.make_instance(self.today, ChoreInstance.STATUS_PENDING, assigned_to=self.alice)
        instance.reassign(self.bob)
        instance.refresh_from_db()
        self.assertEqual(instance.assigned_to, self.bob)
