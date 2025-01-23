from fastapi import HTTPException, status

from utils.status_code import StatusCodeEnum


class NotFoundException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.NOT_FOUND.value}


class DuplicateException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.DUPLICATE.value}


class InProgressException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.IN_PROGRESS.value}


class OTPException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.OTP_ERROR.value}

class IncorrectPwdException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.INCORRECT_PWD.value}


class DiffPwdException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.DIFF_PWD.value}


class TokenException(HTTPException):
    def __init__(self, detail: str) -> None:
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.TOKEN.value}


class GoogleAuthException(HTTPException):
    def __init__(self, detail: str) -> None:
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.GOOGLE_AUTH.value}


class LoginExpiredException(HTTPException):
    def __init__(self, detail: str) -> None:
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.LOGIN_EXPIRED.value}


class UpdateException(HTTPException):
    def __init__(self, detail: str) -> None:
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.UPDATE_ERROR.value}


class ForbiddenException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.FORBIDDEN_REQUEST.value}


class BadRequestException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_418_IM_A_TEAPOT
        self.detail = detail
        self.headers = {"X-Error": StatusCodeEnum.BAD_REQUEST.value}
