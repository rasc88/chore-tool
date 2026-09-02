from .models import ChoreInstance


def notifications(request):
    return {'flagged_count': ChoreInstance.objects.flagged().count()}
