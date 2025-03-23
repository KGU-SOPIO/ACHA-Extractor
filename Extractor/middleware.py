import logging
import time
from typing import Callable

from django.http import HttpRequest, HttpResponse


class PerformanceMiddleware:
    def __init__(self, getResponse: Callable[[HttpRequest], HttpResponse]):
        self.getResponse = getResponse
        self.logger = logging.getLogger("performance")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        startTime = time.perf_counter()
        response = self.getResponse(request)
        elapsedTime = (time.perf_counter() - startTime) * 1000

        if request.path.startswith("/v"):
            self.logger.info(
                "API Request Completed",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "time": f"{elapsedTime}ms",
                    "status": response.status_code,
                },
            )
        return response
