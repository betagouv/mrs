from django import http


class NoSameSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        institution = getattr(response, 'institution', None)
        if not institution:
            return response

        if institution.dynamic_allow:
            if 'origin' not in request.GET:
                return http.HttpResponseBadRequest('"origin" required in GET')
            origin = request.GET['origin']
        else:
            origin = self.institution.origin

        allow_origin = '/'.join(origin.split('/')[:3])

        response['X-Frame-Options'] = 'ALLOW-FROM ' + allow_origin
        response['Access-Control-Allow-Origin'] = allow_origin

        csp = response['Content-Security-Policy']
        response['Content-Security-Policy'] = csp.replace(
            "frame-ancestors 'self'",
            'frame-ancestors ' + allow_origin,
        )

        # samesite is not going to work embedded in an iframe :)
        if 'sessionid' in response.cookies:
            del response.cookies['sessionid']['samesite']
        if 'csrftoken' in response.cookies:
            del response.cookies['csrftoken']['samesite']

        return response
