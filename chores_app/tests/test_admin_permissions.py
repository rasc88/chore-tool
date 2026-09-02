from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from chores_app.admin import ChoreAdmin, ChoreInstanceAdmin
from chores_app.models import Chore, ChoreInstance, Household, Profile


class AdminPermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.household = Household.objects.create(name='Smith Family')
        self.chore_admin = ChoreAdmin(Chore, admin.site)
        self.chore_instance_admin = ChoreInstanceAdmin(ChoreInstance, admin.site)

    def _request_for(self, user):
        request = self.factory.get('/')
        request.user = user
        return request

    def test_admin_profile_has_all_permissions_for_chore_admin(self):
        user = get_user_model().objects.create_user(username='alice', password='pw12345')
        Profile.objects.create(user=user, household=self.household, is_admin=True)
        request = self._request_for(user)

        self.assertTrue(self.chore_admin.has_add_permission(request))
        self.assertTrue(self.chore_admin.has_change_permission(request))
        self.assertTrue(self.chore_admin.has_delete_permission(request))

    def test_admin_profile_has_all_permissions_for_chore_instance_admin(self):
        user = get_user_model().objects.create_user(username='alice', password='pw12345')
        Profile.objects.create(user=user, household=self.household, is_admin=True)
        request = self._request_for(user)

        self.assertTrue(self.chore_instance_admin.has_add_permission(request))
        self.assertTrue(self.chore_instance_admin.has_change_permission(request))
        self.assertTrue(self.chore_instance_admin.has_delete_permission(request))

    def test_non_admin_profile_has_no_permissions_for_chore_admin(self):
        user = get_user_model().objects.create_user(username='bob', password='pw12345')
        Profile.objects.create(user=user, household=self.household, is_admin=False)
        request = self._request_for(user)

        self.assertFalse(self.chore_admin.has_add_permission(request))
        self.assertFalse(self.chore_admin.has_change_permission(request))
        self.assertFalse(self.chore_admin.has_delete_permission(request))

    def test_non_admin_profile_has_no_permissions_for_chore_instance_admin(self):
        user = get_user_model().objects.create_user(username='bob', password='pw12345')
        Profile.objects.create(user=user, household=self.household, is_admin=False)
        request = self._request_for(user)

        self.assertFalse(self.chore_instance_admin.has_add_permission(request))
        self.assertFalse(self.chore_instance_admin.has_change_permission(request))
        self.assertFalse(self.chore_instance_admin.has_delete_permission(request))

    def test_missing_profile_has_no_permissions_for_chore_admin(self):
        user = get_user_model().objects.create_user(username='carol', password='pw12345')
        request = self._request_for(user)

        self.assertFalse(self.chore_admin.has_add_permission(request))
        self.assertFalse(self.chore_admin.has_change_permission(request))
        self.assertFalse(self.chore_admin.has_delete_permission(request))

    def test_missing_profile_has_no_permissions_for_chore_instance_admin(self):
        user = get_user_model().objects.create_user(username='carol', password='pw12345')
        request = self._request_for(user)

        self.assertFalse(self.chore_instance_admin.has_add_permission(request))
        self.assertFalse(self.chore_instance_admin.has_change_permission(request))
        self.assertFalse(self.chore_instance_admin.has_delete_permission(request))

    def test_household_admin_registration_uses_default_permissions(self):
        user = get_user_model().objects.create_superuser(
            username='dave', email='dave@example.com', password='pw12345',
        )
        request = self._request_for(user)
        household_admin = admin.site._registry[Household]

        self.assertTrue(household_admin.has_add_permission(request))
