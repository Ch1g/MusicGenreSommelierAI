class AppError(Exception):
    status_code: int


class ValidationError(AppError):
    status_code = 422


class EmailAlreadyExistsError(AppError):
    status_code = 409


class AuthenticationError(AppError):
    status_code = 401


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403
