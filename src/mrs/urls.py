from django.contrib import admin
from django.views import generic
from django.urls import path

urlpatterns = [
    path('', generic.TemplateView.as_view(template_name='home.html')),
    path('admin/', admin.site.urls),
]
