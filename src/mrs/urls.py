from crudlfap import crudlfap

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from contact.views import ContactView
from mrsrequest.views import MRSRequestCreateView

from . import views

admin.site.site_header = 'MRS Admin'
admin.site.site_title = 'MRS Admin'

crudlfap.site.title = 'MRS Admin'

urlpatterns = [
    crudlfap.site.get_urlpattern('newadmin'),
    path('', MRSRequestCreateView.as_view(
        template_name='index.html'), name='index'),
    path('demande', MRSRequestCreateView.as_view(), name='demande'),
    path('contact', ContactView.as_view(), name='contact'),
    path('mentions-legales', views.LegalView.as_view(), name='legal'),
    path('faq', views.FaqView.as_view(), name='faq'),
    path('manifest.json', views.StaticView.as_view(
        path='manifest.json', content_type='application/manifest+json',
    )),
    path('stats/', views.generic.RedirectView.as_view(
        url='/stats', permanent=True)),
    path('stats', views.StatisticsView.as_view(), name='statistics'),
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
