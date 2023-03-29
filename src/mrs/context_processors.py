import json
from urllib.parse import urlparse

from django.conf import settings as s
from django.urls import reverse


def strip_password(url):
    if not url:
        return url

    parsed = urlparse(url)
    replaced = parsed._replace(
        netloc="{}@{}".format(parsed.username, parsed.hostname))
    return replaced.geturl()


def settings(request):
    return dict(
        INSTANCE=s.INSTANCE,
        PREFIX=s.PREFIX,
        RELEASE=s.RELEASE,
        SENTRY_DSN=s.SENTRY_DSN,
    )


def header_links(request):
    url_name = request.resolver_match.url_name
    header_links = (
        dict(url=reverse('demande'), alias='demander un remboursement',
             active=url_name == 'demande', couleur='rose'),
        dict(url=reverse('faq'), alias='aide',
             active=url_name == 'faq', couleur='bleu'),
    )

    return dict(
        header_links=header_links,
        header_links_json=json.dumps(header_links),
    )
