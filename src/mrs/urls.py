from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from contact.views import ContactView
from mrsrequest.views import MRSRequestCreateView

admin.site.site_header = 'MRS Admin'
admin.site.site_title = 'MRS Admin'

urlpatterns = [
    path('', MRSRequestCreateView.as_view(
        template_name='index.html'), name='index'),
    path('', include('mrspage.urls', namespace='mrspage')),
    path('demande', MRSRequestCreateView.as_view(), name='demande'),
    path('contact', ContactView.as_view(), name='contact'),
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
