from crudlfap import shortcuts as crudlfap

from django.conf import settings
from django.contrib import admin
from django.views.decorators.cache import cache_page
from django.urls import include, path

from contact.views import ContactView
from mrsrequest.views import MRSRequestCreateView
from mrsrequest.views import MRSRequestCancelView
from mrs.settings import TITLE_SUFFIX

from . import views

admin.site.site_header = 'MRS Admin' + TITLE_SUFFIX
admin.site.site_title = 'MRS Admin' + TITLE_SUFFIX

crudlfap.site.title = 'MRS Admin' + TITLE_SUFFIX
crudlfap.site.urlpath = 'admin'
crudlfap.site.views['home'] = views.Dashboard

urlpatterns = [
    crudlfap.site.get_urlpattern(),
    path('', MRSRequestCreateView.as_view(
        template_name='index.html'), name='index'),
    path('demande', MRSRequestCreateView.as_view(), name='demande'),
    path('demande/<update_token>/annuler/confirm',
         MRSRequestCancelView.as_view(),
         name='confirm_cancel_demande'),
    path('demande/<update_token>/annuler', MRSRequestCancelView.as_view(),
         name='cancel_demande'),
    path('contact', ContactView.as_view(), name='contact'),
    path('mentions-legales', views.LegalView.as_view(), name='legal'),
    path('faq', views.FaqView.as_view(), name='faq'),
    path('manifest.json', views.StaticView.as_view(
        path='manifest.json',
        content_type='application/manifest+json',
        stream=False,
    )),
    path('explorer/', include('explorer.urls')),
    path('stats/', views.generic.RedirectView.as_view(
        url='/stats', permanent=True)),
    path(
        'stats',
        cache_page(60 * 24)(views.StatisticsView.as_view()),
        name='statistics'
    ),
    path('contact/', include('contact.urls', namespace='contact')),
    path('mrsrequest/', include('mrsrequest.urls', namespace='mrsrequest')),
    path('institution/', include('institution.urls', namespace='institution')),
    path('oldadmin/', admin.site.urls),
]

if 'debug_toolbar' in settings.INSTALLED_APPS and settings.DEBUG:  # noqa pragma: no cover
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
