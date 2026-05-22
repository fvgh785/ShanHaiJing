"""
API响应装饰器
"""

import functools
import json
from flask import request, jsonify
from .exceptions import ValidationException, handle_validation_errors


def api_response(success=True, data=None, message=None, code=None, status_code=200):
    """统一的API响应格式装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # 如果函数已经返回了响应，直接返回
                if isinstance(result, tuple) and len(result) >= 2 and isinstance(result[1], int):
                    return result
                
                # 构建统一响应格式
                response_data = {
                    "success": success,
                    "timestamp": "2026-05-22T10:00:00Z"
                }
                
                if data is not None:
                    response_data["data"] = result if success else data
                
                if message:
                    response_data["message"] = message
                
                if code:
                    response_data["code"] = code
                
                # 添加请求信息（用于调试）
                if request:
                    response_data["request"] = {
                        "method": request.method,
                        "path": request.path,
                        "query_params": dict(request.args),
                        "user_agent": request.headers.get('User-Agent')
                    }
                
                return jsonify(response_data), status_code
                
            except Exception as e:
                # 如果异常是自定义异常，直接处理
                from .exceptions import BaseException, create_error_response
                if isinstance(e, BaseException):
                    return create_error_response(e)
                
                # 其他异常转换为通用错误
                from .exceptions import BaseException as GenericBaseException
                return create_error_response(GenericBaseException(
                    "An unexpected error occurred.",
                    details={"error_type": type(e).__name__, "original_error": str(e)}
                ))
        
        return wrapper
    return decorator


def validate_data(schema):
    """数据验证装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json(silent=True)
                if not data:
                    from .exceptions import BadRequestException
                    raise BadRequestException("Request body is required")
                
                # 这里可以集成更复杂的验证逻辑，如Pydantic等
                # 目前进行简单的字段验证
                errors = {}
                
                # 示例：验证必填字段
                required_fields = schema.get('required', [])
                for field in required_fields:
                    if field not in data or data[field] is None or data[field] == '':
                        errors[field] = f"{field} is required"
                
                # 示例：验证字段类型
                field_types = schema.get('types', {})
                for field, expected_type in field_types.items():
                    if field in data and data[field] is not None:
                        if expected_type == 'integer' and not isinstance(data[field], int):
                            errors[field] = f"{field} must be an integer"
                        elif expected_type == 'string' and not isinstance(data[field], str):
                            errors[field] = f"{field} must be a string"
                        elif expected_type == 'array' and not isinstance(data[field], list):
                            errors[field] = f"{field} must be an array"
                
                if errors:
                    from .exceptions import ValidationException
                    raise ValidationException("Validation failed", details=handle_validation_errors(errors))
                
                return func(*args, **kwargs)
                
            except Exception as e:
                # 如果异常是自定义异常，直接处理
                from .exceptions import BaseException, create_error_response
                if isinstance(e, BaseException):
                    return create_error_response(e)
                
                # 其他异常转换为通用错误
                from .exceptions import BaseException as GenericBaseException
                return create_error_response(GenericBaseException(
                    "Validation error occurred.",
                    details={"error_type": type(e).__name__, "original_error": str(e)}
                ))
        
        return wrapper
    return decorator


def handle_database_errors(func):
    """数据库错误处理装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            from .exceptions import DatabaseException
            raise DatabaseException(
                "Database operation failed",
                details={"error": str(e), "operation": func.__name__}
            )
    return wrapper


def log_api_call(func):
    """API调用日志装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import logging
        from flask import request
        
        logger = logging.getLogger(__name__)
        
        # 记录请求信息
        logger.info(f"API Call: {request.method} {request.path}", extra={
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "content_type": request.headers.get('Content-Type')
        })
        
        try:
            result = func(*args, **kwargs)
            
            # 记录成功响应
            logger.info(f"API Success: {request.method} {request.path}", extra={
                "status": "success",
                "response_data": str(result)[:200] if hasattr(result, 'get') else "No response data"
            })
            
            return result
            
        except Exception as e:
            # 记录错误响应
            logger.error(f"API Error: {request.method} {request.path}", extra={
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
    
    return wrapper


def require_api_key(func):
    """API密钥验证装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request
        from .exceptions import UnauthorizedException
        
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            raise UnauthorizedException("API key is required")
        
        # 这里可以添加API密钥验证逻辑
        # 例如：检查API密钥是否有效，是否在有效期内等
        
        return func(*args, **kwargs)
    
    return wrapper