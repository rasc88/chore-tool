from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase

from chores_app.models import Household, Profile


class HouseholdModelTests(TestCase):
    def test_create_household_with_name(self):
        household = Household.objects.create(name='Smith Family')

        self.assertEqual(household.name, 'Smith Family')

    def test_str_returns_name(self):
        household = Household.objects.create(name='Smith Family')

        self.assertEqual(str(household), household.name)


class ProfileModelTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.user = get_user_model().objects.create_user(username='alice', password='pw12345')

    def test_create_profile_requires_user_and_household(self):
        profile = Profile.objects.create(user=self.user, household=self.household)

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.household, self.household)

    def test_is_admin_defaults_to_false(self):
        profile = Profile.objects.create(user=self.user, household=self.household)

        self.assertFalse(profile.is_admin)

    def test_str_returns_username(self):
        profile = Profile.objects.create(user=self.user, household=self.household)

        self.assertEqual(str(profile), self.user.get_username())

    def test_duplicate_profile_for_same_user_raises_integrity_error(self):
        Profile.objects.create(user=self.user, household=self.household)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Profile.objects.create(user=self.user, household=self.household)

        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
