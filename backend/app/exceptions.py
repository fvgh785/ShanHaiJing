"""
自定义异常类
"""

from flask import jsonify


class BaseException(Exception):
    """基础异常类"""
    def __init__(self, message, code="INTERNAL_ERROR", status_code=500, details=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class BadRequestException(BaseException):
    """400 错误：请求参数错误"""
    def __init__(self, message="Bad request", details=None):
        super().__init__(message, "BAD_REQUEST", 400, details)


class NotFoundException(BaseException):
    """404 错误：资源不存在"""
    def __init__(self, message="Resource not found", details=None):
        super().__init__(message, "NOT_FOUND", 404, details)


class UnauthorizedException(BaseException):
    """401 错误：未授权"""
    def __init__(self, message="Unauthorized", details=None):
        super().__init__(message, "UNAUTHORIZED", 401, details)


class ForbiddenException(BaseException):
    """403 错误：禁止访问"""
    def __init__(self, message="Forbidden", details=None):
        super().__init__(message, "FORBIDDEN", 403, details)


class ConflictException(BaseException):
    """409 错误：资源冲突"""
    def __init__(self, message="Conflict", details=None):
        super().__init__(message, "CONFLICT", 409, details)


class UnprocessableEntityException(BaseException):
    """422 错误：无法处理的实体"""
    def __init__(self, message="Unprocessable entity", details=None):
        super().__init__(message, "UNPROCESSABLE_ENTITY", 422, details)


class ValidationException(BaseException):
    """数据验证错误"""
    def __init__(self, message="Validation failed", details=None):
        super().__init__(message, "VALIDATION_ERROR", 422, details)


class DatabaseException(BaseException):
    """数据库错误"""
    def __init__(self, message="Database error", details=None):
        super().__init__(message, "DATABASE_ERROR", 500, details)


class ExternalServiceException(BaseException):
    """外部服务错误"""
    def __init__(self, message="External service error", details=None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", 502, details)


def create_error_response(exception):
    """创建统一的错误响应"""
    response = {
        "error": {
            "code": exception.code,
            "message": exception.message,
            "timestamp": "2026-05-22T10:00:00Z"
        }
    }
    
    # 如果有详细信息，添加到响应中
    if exception.details:
        response["error"]["details"] = exception.details
    
    # 添加请求ID（如果有）
    if hasattr(exception, 'request_id'):
        response["error"]["request_id"] = exception.request_id
    
    return jsonify(response), exception.status_code


def handle_validation_errors(errors):
    """处理验证错误"""
    if isinstance(errors, dict):
        return {
            "field_errors": errors
        }
    elif isinstance(errors, list):
        return {
            "general_errors": errors
        }
    else:
        return {
            "general_errors": [str(errors)]
        }