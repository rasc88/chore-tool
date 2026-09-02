from django.urls import path

from . import views

app_name = 'chores'

urlpatterns = [
    path('', views.status_board, name='status_board'),
    path('history/', views.history, name='history'),
    path('ownership/', views.ownership_map, name='ownership_map'),
    path('instances/<int:pk>/claim/', views.claim_instance, name='claim_instance'),
    path('instances/<int:pk>/mark-done/', views.mark_done, name='mark_done'),
]
