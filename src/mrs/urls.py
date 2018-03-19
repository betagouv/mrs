from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from graphene_django.views import GraphQLView

from contact.views import ContactView
from mrsrequest.views import MRSRequestCreateView

from . import views
from .schema import schema

admin.site.site_header = 'MRS Admin'
admin.site.site_title = 'MRS Admin'

urlpatterns = [
    path('', MRSRequestCreateView.as_view(
        template_name='index.html'), name='index'),
    path('', include('mrspage.urls', namespace='mrspage')),
    path('demande', MRSRequestCreateView.as_view(), name='demande'),
    path('contact', ContactView.as_view(), name='contact'),
    path('mentions-legales', views.LegalView.as_view(), name='legal'),
    path('faq', views.FaqView.as_view(), name='faq'),
    path('contact/', include('contact.urls', namespace='contact')),
    path('mrsrequest/', include('mrsrequest.urls', namespace='mrsrequest')),
    path('institution/', include('institution.urls', namespace='institution')),
    path('admin/', admin.site.urls),
    path('graphql', GraphQLView.as_view(graphiql=True, schema=schema)),
]

if 'debug_toolbar' in settings.INSTALLED_APPS and settings.DEBUG:  # noqa pragma: no cover
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
