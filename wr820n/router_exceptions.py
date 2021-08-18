class RouterException(Exception):
    """Base class for router exceptions"""
    pass


class WrongPasswordException(RouterException):
    """Raises when attempt after generation a new session keys failed"""
    pass


class UnauthorizedAccessException(RouterException):
    """Raises when attempt to request failed"""
    pass


class IncorrectResponseFormatException(RouterException):
    """Raises when received response has a incorrect format"""
    pass


class RequestException(RouterException):
    """Raises when error occurred during the request"""
    pass


class BadUserData(RouterException):
    """Raises when router user's info has a unexpected data"""
    pass
