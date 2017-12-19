from django.conf import settings
from django.views import generic
from django.urls import include, path, reverse_lazy

from material.frontend import urls as frontend_urls
urlpatterns = [
    path('', generic.RedirectView.as_view(
        url=reverse_lazy('mrsrequest:wizard'))
    ),
    path('', include(frontend_urls)),
]

if 'debug_toolbar' in settings.INSTALLED_APPS and settings.DEBUG:  # noqa pragma: no cover
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
