import json
import logging

logger = logging.getLogger("api.requests")


class RequestLoggingMiddleware:
    """Log all API requests for debugging and audit purposes."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details
        body = ""
        if request.body:
            try:
                body = json.loads(request.body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                body = request.body.decode("utf-8", errors="replace")

        logger.info(
            "API Request: %s %s | User: %s | Body: %s | Headers: %s",
            request.method,
            request.get_full_path(),
            getattr(request, "user", "anonymous"),
            body,
            dict(request.headers),
        )

        response = self.get_response(request)

        logger.info(
            "API Response: %s %s | Status: %s",
            request.method,
            request.get_full_path(),
            response.status_code,
        )

        return response
