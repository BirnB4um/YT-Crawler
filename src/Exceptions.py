
from datetime import datetime
import traceback

from logger import CrawlLogger
logger = CrawlLogger().logger


class CrawlerException(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details

        self.log()

    def log(self):
        msg = f"{self.__class__.__name__}: {self.args[0]}"
        if self.details:
            msg += f"\nDetails: {self.details}"

        #add traceback to the log message
        tb = traceback.format_exc()
        if tb:
            msg += f"\nTraceback:\n{tb}"

        logger.error(msg)


class BadStatusCode(CrawlerException):
    def __init__(self, status_code, details=None):
        self.status_code = status_code
        super().__init__(f"{status_code}", details=details)

class WrongResponseFormat(CrawlerException):
    def __init__(self, response_format, details=None):
        self.response_format = response_format
        super().__init__(f"{response_format}", details=details)

class ParsingError(CrawlerException):
    def __init__(self, data_to_parse, details=None):
        super().__init__(f"Couldn't parse the following data:\n{data_to_parse}", details=details)

class NoDataFound(CrawlerException):
    def __init__(self, message, details=None):
        super().__init__(f"{message}", details=details)

class UnexpectedFormat(CrawlerException):
    def __init__(self, message, details=None):
        super().__init__(f"{message}", details=details)

class NoVideosFound(CrawlerException):
    def __init__(self, message, details=None):
        super().__init__(f"{message}", details=details)