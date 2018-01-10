from django.urls import path

from . import views


app_name = 'contact'
urlpatterns = [
    path(
        'create/',
        views.ContactView.as_view(),
        name='contact_create'
    ),
]
