from django.contrib import admin

from .models import Chore, ChoreInstance, Household, Profile

admin.site.register(Household)
admin.site.register(Profile)


def _is_household_admin(request):
    try:
        return request.user.profile.is_admin
    except Profile.DoesNotExist:
        return False


class AdminOnlyModelAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return _is_household_admin(request)

    def has_change_permission(self, request, obj=None):
        return _is_household_admin(request)

    def has_delete_permission(self, request, obj=None):
        return _is_household_admin(request)


@admin.register(Chore)
class ChoreAdmin(AdminOnlyModelAdmin):
    pass


@admin.register(ChoreInstance)
class ChoreInstanceAdmin(AdminOnlyModelAdmin):
    pass
