import base64
import binascii
import os
from urllib.parse import unquote_plus

from django import http
from django.conf import settings
from django.contrib.auth import authenticate


class HttpResponseUnauthorized(http.HttpResponse):
    status_code = 401

    def __init__(self):
        super(HttpResponseUnauthorized, self).__init__(
            """<html><head><title>Basic auth required</title></head>
               <body><h1>Authorization Required</h1></body></html>""",
        )
        realm = getattr(settings, 'BASICAUTH_REALM', 'Sécurité MRS')
        self['WWW-Authenticate'] = 'Basic realm="{}"'.format(realm)


def extract_basicauth(authorization_header, encoding='utf-8'):
    splitted = authorization_header.split(' ')
    if len(splitted) != 2:
        return None

    auth_type, auth_string = splitted

    if 'basic' != auth_type.lower():
        return None

    try:
        b64_decoded = base64.b64decode(auth_string)
    except (TypeError, binascii.Error):
        return None
    try:
        auth_string_decoded = b64_decoded.decode(encoding)
    except UnicodeDecodeError:
        return None

    splitted = auth_string_decoded.split(':')

    if len(splitted) != 2:
        return None

    username, password = map(unquote_plus, splitted)
    return username, password


class BasicAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def authorize(self, request):
        if not os.getenv('BASICAUTH_ENABLE', False):
            # Not to use this env
            return True

        if request.session.get('authorized', False):
            return True

        if request.user.is_authenticated:
            return True

        if request.session.get('authorized', False):
            return True

        if 'HTTP_AUTHORIZATION' not in request.META:
            return False

        authorization_header = request.META['HTTP_AUTHORIZATION']
        ret = extract_basicauth(authorization_header)
        if not ret:
            return False

        username, password = ret

        user = authenticate(username=username, password=password)

        if user:
            request.session['authorized'] = True
            return True

    def __call__(self, request):
        if not self.authorize(request):
            return HttpResponseUnauthorized()
        return self.get_response(request)
