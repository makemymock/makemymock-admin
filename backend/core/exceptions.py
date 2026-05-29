from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception. Subclass to define domain-specific errors."""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


# ---- Auth ----
class InvalidCredentials(AppException):
    def __init__(self, detail: str = "Invalid email or password."):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED)


class InvalidToken(AppException):
    def __init__(self, detail: str = "Invalid or expired token."):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED)


class Forbidden(AppException):
    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(detail, status.HTTP_403_FORBIDDEN)


# ---- Users ----
class UserNotFound(AppException):
    def __init__(self, detail: str = "User not found."):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


# ---- Questions ----
class QuestionNotFound(AppException):
    def __init__(self, detail: str = "Question not found."):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


class CatalogNotFound(AppException):
    def __init__(self, detail: str = "Catalog entry not found."):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


# ---- Promo email ----
class EmailDispatchFailed(AppException):
    def __init__(self, detail: str = "Failed to dispatch email."):
        super().__init__(detail, status.HTTP_502_BAD_GATEWAY)


class NoRecipients(AppException):
    def __init__(self, detail: str = "At least one recipient email is required."):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)


class TooManyRecipients(AppException):
    def __init__(self, detail: str = "Too many recipients in a single batch."):
        super().__init__(detail, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


# ---- Contests ----
class ContestNotFound(AppException):
    def __init__(self, detail: str = "Contest not found."):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


class ContestOverlap(AppException):
    def __init__(self, detail: str = "Contest time overlaps an existing contest."):
        super().__init__(detail, status.HTTP_409_CONFLICT)


class ContestNotEditable(AppException):
    def __init__(self, detail: str = "Contest cannot be edited once it has started."):
        super().__init__(detail, status.HTTP_409_CONFLICT)


class ContestInvalid(AppException):
    def __init__(self, detail: str = "Contest payload is invalid."):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)
