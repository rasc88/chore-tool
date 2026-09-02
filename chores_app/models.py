from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Household(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='members')
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_username()


class Chore(models.Model):
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    RECURRENCE_INTERVAL = 'interval'
    RECURRENCE_WEEKDAYS = 'weekdays'
    RECURRENCE_DEADLINE = 'deadline'
    RECURRENCE_TYPE_CHOICES = [
        (RECURRENCE_INTERVAL, 'Fixed interval'),
        (RECURRENCE_WEEKDAYS, 'Specific weekdays'),
        (RECURRENCE_DEADLINE, 'Deadline-based'),
    ]

    ASSIGNMENT_FIXED = 'fixed'
    ASSIGNMENT_ROTATING = 'rotating'
    ASSIGNMENT_POOL = 'pool'
    ASSIGNMENT_TYPE_CHOICES = [
        (ASSIGNMENT_FIXED, 'Fixed'),
        (ASSIGNMENT_ROTATING, 'Rotating'),
        (ASSIGNMENT_POOL, 'Pool'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    recurrence_type = models.CharField(max_length=10, choices=RECURRENCE_TYPE_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    interval_days = models.PositiveIntegerField(null=True, blank=True)
    weekdays = models.CharField(max_length=13, null=True, blank=True)
    assignment_type = models.CharField(max_length=10, choices=ASSIGNMENT_TYPE_CHOICES, default=ASSIGNMENT_POOL)
    fixed_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='fixed_chores',
    )
    rotation_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='rotating_chores',
    )
    rotation_next_index = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def next_due_date(self, from_date):
        if self.recurrence_type == self.RECURRENCE_INTERVAL:
            return from_date + timedelta(days=self.interval_days)

        if self.recurrence_type == self.RECURRENCE_WEEKDAYS:
            target_days = {int(day) for day in self.weekdays.split(',')}
            # ISO weekdays cycle every 7 days, so a match is always found within one week.
            for offset in range(1, 8):
                candidate = from_date + timedelta(days=offset)
                if candidate.isoweekday() in target_days:
                    return candidate

        return from_date

    def create_next_instance(self, from_date=None):
        from_date = from_date or date.today()
        return ChoreInstance.objects.create(
            chore=self,
            due_date=self.next_due_date(from_date),
            assigned_to=self._next_assignee(),
        )

    def _next_assignee(self):
        if self.assignment_type == self.ASSIGNMENT_FIXED:
            return self.fixed_assignee

        if self.assignment_type == self.ASSIGNMENT_ROTATING:
            return self._advance_rotation()

        return None

    def _advance_rotation(self):
        members = self.rotation_members.order_by('id')
        count = members.count()
        if count == 0:
            return None

        # Index into the ordered queryset instead of popping a queue, so
        # membership can change between turns without losing the rotation's position.
        index = self.rotation_next_index % count
        assignee = members[index]
        self.rotation_next_index = (index + 1) % count
        self.save(update_fields=['rotation_next_index'])
        return assignee


class ChoreInstanceQuerySet(models.QuerySet):
    def completed(self):
        return self.filter(status=ChoreInstance.STATUS_DONE).order_by('-completed_at')

    def overdue(self):
        return self.filter(status=ChoreInstance.STATUS_PENDING, due_date__lt=timezone.now().date())

    def unclaimed(self):
        return self.filter(status=ChoreInstance.STATUS_PENDING, assigned_to__isnull=True)

    def flagged(self):
        today = timezone.now().date()
        return self.filter(
            Q(due_date__lt=today) | Q(assigned_to__isnull=True),
            status=ChoreInstance.STATUS_PENDING,
        )

    def escalated(self, days=3):
        # Threshold is a plain default, not a settings knob, per the scope of this task.
        return self.flagged().filter(due_date__lt=timezone.now().date() - timedelta(days=days))


class ChoreInstance(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_DONE = 'done'
    STATUS_OVERDUE = 'overdue'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_DONE, 'Done'),
        (STATUS_OVERDUE, 'Overdue'),
    ]

    objects = models.Manager.from_queryset(ChoreInstanceQuerySet)()

    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name='instances')
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_chore_instances',
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='completed_chore_instances',
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.chore.name} due {self.due_date}'

    @property
    def is_overdue(self):
        return self.status == self.STATUS_PENDING and self.due_date < timezone.now().date()

    @property
    def is_unclaimed(self):
        return self.assigned_to_id is None and self.status == self.STATUS_PENDING

    def claim(self, user):
        if self.assigned_to is not None:
            raise ValueError('instance is already assigned')
        self.assigned_to = user
        self.save(update_fields=['assigned_to'])

    def reassign(self, user):
        self.assigned_to = user
        self.save(update_fields=['assigned_to'])

    def mark_done(self, user):
        self.status = self.STATUS_DONE
        self.completed_by = user
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_by', 'completed_at'])

        # Interval/weekday chores are generated on a schedule elsewhere;
        # only deadline-based chores create their next instance on completion.
        if self.chore.recurrence_type == Chore.RECURRENCE_DEADLINE:
            self.chore.create_next_instance()
