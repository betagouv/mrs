from django.urls import path

from . import views


app_name = 'mrspage'
urlpatterns = [
    path(
        'stats/',
        views.StatisticsView.as_view(),
        name='statistics',
    ),
]
