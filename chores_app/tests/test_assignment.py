from django.contrib.auth import get_user_model
from django.test import TestCase

from chores_app.models import Chore, Household


class FixedAssignmentTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.creator = get_user_model().objects.create_user(username='creator', password='pw12345')
        self.assignee = get_user_model().objects.create_user(username='alice', password='pw12345')
        self.chore = Chore.objects.create(
            name='Wash dishes',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=1,
            created_by=self.creator,
            assignment_type=Chore.ASSIGNMENT_FIXED,
            fixed_assignee=self.assignee,
        )

    def test_create_next_instance_assigns_fixed_assignee(self):
        instance = self.chore.create_next_instance()

        self.assertEqual(instance.assigned_to, self.assignee)


class RotatingAssignmentTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.creator = get_user_model().objects.create_user(username='creator', password='pw12345')
        self.member_a = get_user_model().objects.create_user(username='alice', password='pw12345')
        self.member_b = get_user_model().objects.create_user(username='bob', password='pw12345')
        self.chore = Chore.objects.create(
            name='Wash dishes',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=1,
            created_by=self.creator,
            assignment_type=Chore.ASSIGNMENT_ROTATING,
        )
        self.chore.rotation_members.add(self.member_a, self.member_b)

    def test_rotation_cycles_through_members_in_id_order_wrapping_around(self):
        first_instance = self.chore.create_next_instance()
        second_instance = self.chore.create_next_instance()
        third_instance = self.chore.create_next_instance()

        # Third call wraps back to member_a since only two members are in the pool.
        self.assertEqual(first_instance.assigned_to, self.member_a)
        self.assertEqual(second_instance.assigned_to, self.member_b)
        self.assertEqual(third_instance.assigned_to, self.member_a)

    def test_rotation_next_index_advances_and_wraps(self):
        self.chore.create_next_instance()
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.rotation_next_index, 1)

        self.chore.create_next_instance()
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.rotation_next_index, 0)

    def test_rotation_with_no_members_assigns_none(self):
        self.chore.rotation_members.clear()

        instance = self.chore.create_next_instance()

        self.assertIsNone(instance.assigned_to)


class PoolAssignmentTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.creator = get_user_model().objects.create_user(username='creator', password='pw12345')
        self.chore = Chore.objects.create(
            name='Wash dishes',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=1,
            created_by=self.creator,
            assignment_type=Chore.ASSIGNMENT_POOL,
        )

    def test_create_next_instance_leaves_pool_chore_unassigned(self):
        instance = self.chore.create_next_instance()

        self.assertIsNone(instance.assigned_to)


class ClaimTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.creator = get_user_model().objects.create_user(username='creator', password='pw12345')
        self.claimer = get_user_model().objects.create_user(username='alice', password='pw12345')
        self.other_user = get_user_model().objects.create_user(username='bob', password='pw12345')
        self.chore = Chore.objects.create(
            name='Wash dishes',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=1,
            created_by=self.creator,
            assignment_type=Chore.ASSIGNMENT_POOL,
        )
        self.instance = self.chore.create_next_instance()

    def test_claim_assigns_unassigned_instance_to_user(self):
        self.instance.claim(self.claimer)

        self.assertEqual(self.instance.assigned_to, self.claimer)

    def test_claim_on_already_assigned_instance_raises_value_error(self):
        self.instance.claim(self.claimer)

        with self.assertRaises(ValueError):
            self.instance.claim(self.other_user)

        self.instance.refresh_from_db()
        self.assertEqual(self.instance.assigned_to, self.claimer)
