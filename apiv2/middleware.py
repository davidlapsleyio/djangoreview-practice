import threading

from django.urls import clear_url_caches

_url_lock = threading.Lock()


class APIVersionMiddleware:
    """Middleware to handle API versioning.

    Issue 9: Monkey-patches URLconf at request time — not thread-safe.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        api_version = request.META.get("HTTP_X_API_VERSION", "v1")

        if api_version == "v2":
            # Issue 9: Monkey-patching URLconf is NOT thread-safe
            # Two concurrent requests could stomp on each other
            request.urlconf = "apiv2.urls_v2"
            clear_url_caches()

        response = self.get_response(request)

        # Issue 12: v2 silently changes field names without deprecation headers
        # Should add Deprecation or Sunset headers for changed fields
        if api_version == "v2":
            response["X-API-Version"] = "v2"

        return response
