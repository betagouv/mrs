from django.conf import settings
from django.contrib import admin
from django.views import generic
from django.urls import include, path, reverse_lazy

admin.site.site_header = 'MRS Admin'
admin.site.site_title = 'MRS Admin'

urlpatterns = [
    path('', generic.RedirectView.as_view(
        url=reverse_lazy('mrsrequest:wizard'))
    ),
    path('', include('mrspage.urls', namespace='mrspage')),
    path('contact/', include('contact.urls', namespace='contact')),
    path('mrsrequest/', include('mrsrequest.urls', namespace='mrsrequest')),
    path('institution/', include('institution.urls', namespace='institution')),
    path('admin/', admin.site.urls),
]

if 'debug_toolbar' in settings.INSTALLED_APPS and settings.DEBUG:  # noqa pragma: no cover
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
