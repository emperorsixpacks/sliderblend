import json
import time
from typing import Callable

from fastapi import Request, Response

from sliderblend.pkg.logger import get_logger

logger = get_logger()


class RequestLoggerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for certain paths (like health checks)
        if request.url.path in ["/health", "/favicon.ico"]:
            return await call_next(request)

        # Log request details
        start_time = time.time()

        request_body = await self._get_request_body(request)
        logger.info(
            f"Request: {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'} | "
            f"Headers: {dict(request.headers)} | "
            f"Query: {dict(request.query_params)} | "
            f"Body: {request_body}"
        )

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        process_time = (time.time() - start_time) * 1000
        formatted_time = f"{process_time:.2f}ms"

        # Log response details
        response_body = await self._get_response_body(response)
        logger.info(
            f"Response: {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Time: {formatted_time} | "
            f"Body: {response_body}"
        )

        # Add X-Process-Time header
        response.headers["X-Process-Time"] = formatted_time

        return response

    async def _get_request_body(self, request: Request):
        """Helper to safely extract request body"""
        try:
            body = await request.json()
            return json.dumps(body, indent=2) if body else "{}"
        except json.JSONDecodeError:
            return "Non-JSON body or empty"

    async def _get_response_body(self, response: Response):
        """Helper to safely extract response body"""
        if hasattr(response, "body"):
            body = response.body.decode("utf-8")
            try:
                # Try to pretty print if it's JSON
                json_body = json.loads(body)
                return json.dumps(json_body, indent=2)
            except json.JSONDecodeError:
                return body[:1000]  # Limit to first 1000 chars if not JSON
