from django.contrib import admin
from django.views import generic
from django.urls import include, path, reverse_lazy

urlpatterns = [
    path('', generic.RedirectView.as_view(url=reverse_lazy('transport_create'))),
    path('transport/', include('transport.urls')),
    path('admin/', admin.site.urls),
]
