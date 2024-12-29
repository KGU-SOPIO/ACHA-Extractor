import logging
import traceback

class ExtractorException(Exception):
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        self.content = kwargs.get("content")
        self.errorCode = kwargs.get("errorCode")
        super().__init__(message, *args, **kwargs)

        tracebackInfo = traceback.format_exc()

        logger = logging.getLogger("watchmen")
        logger.error("", exc_info=True, extra={"traceback": tracebackInfo})