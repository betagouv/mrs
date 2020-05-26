

class NoSameSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        allow_origin = getattr(response, 'allow_origin', None)
        if not allow_origin:
            return response

        response['X-Frame-Options'] = 'ALLOW-FROM ' + allow_origin
        response['Access-Control-Allow-Origin'] = allow_origin

        if 'Content-Security-Policy' in response:
            # patch that on institution iframes
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
