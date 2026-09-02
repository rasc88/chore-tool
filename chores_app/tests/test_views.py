from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from chores_app.models import Chore, ChoreInstance, Household


class ViewTestCase(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='Smith Family')
        self.creator = get_user_model().objects.create_user(username='creator', password='pw12345')
        self.user = get_user_model().objects.create_user(username='alice', password='pw12345')
        self.other_user = get_user_model().objects.create_user(username='bob', password='pw12345')
        self.chore = Chore.objects.create(
            name='Wash dishes',
            recurrence_type=Chore.RECURRENCE_INTERVAL,
            interval_days=1,
            created_by=self.creator,
            assignment_type=Chore.ASSIGNMENT_POOL,
        )
        self.instance = self.chore.create_next_instance()
        self.instance.due_date = timezone.now().date()
        self.instance.save(update_fields=['due_date'])


class StatusBoardViewTests(ViewTestCase):
    def test_anonymous_get_redirects_to_login(self):
        response = self.client.get(reverse('chores:status_board'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_logged_in_get_returns_200(self):
        self.client.login(username='alice', password='pw12345')

        response = self.client.get(reverse('chores:status_board'))

        self.assertEqual(response.status_code, 200)

    def test_logged_in_get_includes_seeded_chore_name(self):
        self.client.login(username='alice', password='pw12345')

        response = self.client.get(reverse('chores:status_board'))

        self.assertContains(response, self.chore.name)


class HistoryViewTests(ViewTestCase):
    def test_anonymous_get_redirects_to_login(self):
        response = self.client.get(reverse('chores:history'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_logged_in_get_returns_200(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('chores:history'))

        self.assertEqual(response.status_code, 200)


class OwnershipMapViewTests(ViewTestCase):
    def test_anonymous_get_redirects_to_login(self):
        response = self.client.get(reverse('chores:ownership_map'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_logged_in_get_returns_200(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('chores:ownership_map'))

        self.assertEqual(response.status_code, 200)


class ClaimInstanceViewTests(ViewTestCase):
    def test_anonymous_post_redirects_to_login_and_does_not_claim(self):
        response = self.client.post(reverse('chores:claim_instance', args=[self.instance.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])
        self.instance.refresh_from_db()
        self.assertIsNone(self.instance.assigned_to)

    def test_logged_in_get_returns_405(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('chores:claim_instance', args=[self.instance.pk]))

        self.assertEqual(response.status_code, 405)

    def test_logged_in_post_claims_unassigned_instance(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('chores:claim_instance', args=[self.instance.pk]))

        self.assertEqual(response.status_code, 302)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.assigned_to, self.user)

    def test_logged_in_post_on_already_assigned_instance_does_not_500(self):
        self.instance.claim(self.other_user)
        self.client.force_login(self.user)

        response = self.client.post(reverse('chores:claim_instance', args=[self.instance.pk]))

        self.assertEqual(response.status_code, 302)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.assigned_to, self.other_user)


class MarkDoneViewTests(ViewTestCase):
    def test_anonymous_post_redirects_to_login_and_does_not_mark_done(self):
        response = self.client.post(reverse('chores:mark_done', args=[self.instance.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, ChoreInstance.STATUS_PENDING)

    def test_logged_in_get_returns_405(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('chores:mark_done', args=[self.instance.pk]))

        self.assertEqual(response.status_code, 405)

    def test_logged_in_post_marks_instance_done(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('chores:mark_done', args=[self.instance.pk]))

        self.assertEqual(response.status_code, 302)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, ChoreInstance.STATUS_DONE)
        self.assertEqual(self.instance.completed_by, self.user)


class NotificationsContextProcessorTests(ViewTestCase):
    def test_flagged_count_reflects_unclaimed_instance(self):
        self.chore.instances.all().delete()
        self.chore.create_next_instance()
        self.client.force_login(self.user)

        response = self.client.get(reverse('chores:status_board'))

        self.assertEqual(response.context['flagged_count'], 1)

    def test_flagged_count_reflects_overdue_instance(self):
        overdue_instance = self.instance
        overdue_instance.assigned_to = self.user
        overdue_instance.due_date = timezone.now().date() - timedelta(days=1)
        overdue_instance.save(update_fields=['assigned_to', 'due_date'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('chores:status_board'))

        self.assertEqual(response.context['flagged_count'], 1)
