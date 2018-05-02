import json
import os
from urllib.parse import urlparse

from django.conf import settings as s
from django.urls import reverse


def strip_password(url):
    parsed = urlparse(url)
    replaced = parsed._replace(
        netloc="{}@{}".format(parsed.username, parsed.hostname))
    return replaced.geturl()


def settings(request):
    if s.RAVEN_CONFIG.get('dsn'):
        raven_dsn = strip_password(s.RAVEN_CONFIG['dsn'])
    else:
        raven_dsn = ''

    return dict(
        settings=dict(
            INSTANCE=os.getenv('INSTANCE'),
            SENTRY_DSN=raven_dsn,
        )
    )


def header_links(request):
    header_links = (
        dict(url=reverse('index'), alias='fonctionnement'),
        dict(url=reverse('demande'), alias='formulaire'),
        dict(url=reverse('faq'), alias='faq'),
        dict(url=reverse('contact'), alias='contact'),
    )

    return dict(
        header_links=header_links,
        header_links_json=json.dumps(header_links),
    )
