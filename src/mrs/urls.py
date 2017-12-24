from django.conf import settings
from django.contrib import admin
from django.views import generic
from django.urls import include, path, reverse_lazy


urlpatterns = [
    path('', generic.RedirectView.as_view(
        url=reverse_lazy('mrsrequest:wizard'))
    ),
    path('pmt/', include('pmt.urls', namespace='pmt')),
    path('mrsrequest/', include('mrsrequest.urls', namespace='mrsrequest')),
    path('transport/', include('transport.urls', namespace='transport')),
    path('admin/', admin.site.urls),
]

if 'debug_toolbar' in settings.INSTALLED_APPS and settings.DEBUG:  # noqa pragma: no cover
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
