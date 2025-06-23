# middleware.py
import logging
import uuid
from django.utils.deprecation import MiddlewareMixin
from ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.trace_id = uuid.uuid4().hex
        logger.info(f"[{request.trace_id}] Request start: {request.method} {request.path}")

    def process_response(self, request, response):
        logger.info(f"[{request.trace_id}] Response: {response.status_code}")
        return response