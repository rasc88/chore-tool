from itertools import groupby

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ChoreInstance


@login_required
def status_board(request):
    today = timezone.now().date()
    instances = ChoreInstance.objects.select_related('chore', 'assigned_to').order_by('due_date')
    todays_instances = [instance for instance in instances if instance.due_date == today or instance.is_overdue]
    context = {
        'pending': [i for i in todays_instances if i.status == ChoreInstance.STATUS_PENDING and not i.is_overdue],
        'done': [i for i in todays_instances if i.status == ChoreInstance.STATUS_DONE],
        'overdue': [i for i in todays_instances if i.is_overdue],
    }
    return render(request, 'chores/status_board.html', context)


@login_required
def history(request):
    completed_instances = ChoreInstance.objects.select_related('chore', 'completed_by').completed()
    return render(request, 'chores/history.html', {'completed_instances': completed_instances})


@login_required
def ownership_map(request):
    assigned_instances = ChoreInstance.objects.select_related('chore', 'assigned_to').filter(
        status=ChoreInstance.STATUS_PENDING,
        assigned_to__isnull=False,
    ).order_by('assigned_to__username', 'due_date')
    grouped = groupby(assigned_instances, key=lambda instance: instance.assigned_to)
    ownership = [(person, list(instances)) for person, instances in grouped]
    return render(request, 'chores/ownership_map.html', {'ownership': ownership})


@login_required
@require_POST
def claim_instance(request, pk):
    instance = get_object_or_404(ChoreInstance, pk=pk)
    try:
        instance.claim(request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect(reverse('chores:status_board'))


@login_required
@require_POST
def mark_done(request, pk):
    instance = get_object_or_404(ChoreInstance, pk=pk)
    instance.mark_done(request.user)
    return redirect(reverse('chores:status_board'))
