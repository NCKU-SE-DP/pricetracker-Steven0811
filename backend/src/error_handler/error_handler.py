from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
import sentry_sdk
import traceback
from src.crawler.exceptions import DomainMismatchException
from src.error_handler.logger import Logger

class ErrorHandler:
    def __init__(self, error, code: int, message: str):
        self.code = code
        self.message = message
        self.error = error

    def catch_error(self, request: Request):
        sentry_sdk.capture_exception(self.error)
        tb = traceback.extract_tb(self.error.__traceback__)
        filename, lineno, _, _ = tb[-1]
        logger = Logger("ErrorHandler", "catch_error").get_logger()
        if self.code == 401 or self.code == 400:
            logger.warning(f"Client error in {filename} at line {lineno}: {self.message}")
        else:
            logger.error(f"System error in {filename} at line {lineno}: {self.message}")
        return JSONResponse(status_code=self.code, content={"message": self.message})


class HTTPExceptionHandler(ErrorHandler):
    def __init__(self, error: HTTPException):
        super().__init__(error, error.status_code, error.detail)

    def handle_http_exception(self, request: Request):
        return self.catch_error(request)


class ValueErrorHandler(ErrorHandler):
    def __init__(self, error: ValueError):
        super().__init__(error, 400, str(error))

    def handle_value_error(self, request: Request):
        return self.catch_error(request)


class AttributeErrorHandler(ErrorHandler):
    def __init__(self, error: AttributeError):
        super().__init__(error, 400, str(error))

    def handle_attribute_error(self, request: Request):
        return self.catch_error(request)


class DomainMismatchHandler(ErrorHandler):
    def __init__(self, error: DomainMismatchException):
        super().__init__(error, 400, str(error))

    def handle_domain_mismatch(self, request: Request):
        return self.catch_error(request)