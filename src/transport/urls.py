from django.urls import path

from . import views


urlpatterns = [
    path('create/', views.TransportCreateView.as_view(), name='transport_create'),
]
