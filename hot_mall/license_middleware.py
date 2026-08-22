from django.conf import settings
from django.http import JsonResponse

from .license import LicenseError, load_license


class LicenseMiddleware:
    """Block every application request until the signed license is valid."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            public_key = getattr(settings, 'LICENSE_PUBLIC_KEY', '')
            public_key_file = getattr(settings, 'LICENSE_PUBLIC_KEY_FILE', '')
            if public_key_file:
                with open(public_key_file, 'r', encoding='ascii') as key_file:
                    public_key = key_file.read()
            payload = load_license(
                settings.LICENSE_FILE,
                public_key,
            )
        except (LicenseError, OSError) as error:
            return JsonResponse(
                {'detail': '系统授权无效，暂不可访问', 'reason': str(error)},
                status=403,
            )

        request.license = payload
        return self.get_response(request)
