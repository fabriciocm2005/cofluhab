from django.conf import settings
from django.shortcuts import redirect


class RequireLoginMiddleware:
    """Force authentication on all non-exempt routes."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_prefixes = (
            '/login/',
            '/logout/',
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
        )

    def __call__(self, request):
        path = request.path

        if request.user.is_authenticated:
            return self.get_response(request)

        if any(path.startswith(prefix) for prefix in self.exempt_prefixes):
            return self.get_response(request)

        login_url = settings.LOGIN_URL
        next_url = request.get_full_path()
        return redirect(f'{login_url}?next={next_url}')
