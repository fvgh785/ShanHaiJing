from flask import jsonify
from .exceptions import BaseException, create_error_response


def register_error_handlers(app):
    """注册全局错误处理器"""
    
    # 处理自定义异常
    @app.errorhandler(BaseException)
    def handle_base_exception(e):
        return create_error_response(e)
    
    @app.errorhandler(400)
    def bad_request(e):
        from .exceptions import BadRequestException
        return create_error_response(BadRequestException(
            str(e.description) if hasattr(e, "description") else str(e)
        ))

    @app.errorhandler(404)
    def not_found(e):
        from .exceptions import NotFoundException
        return create_error_response(NotFoundException(
            "The requested resource was not found."
        ))

    @app.errorhandler(405)
    def method_not_allowed(e):
        from .exceptions import BadRequestException
        return create_error_response(BadRequestException(
            "The method is not allowed for the requested URL."
        ))

    @app.errorhandler(500)
    def internal_error(e):
        from .exceptions import DatabaseException
        return create_error_response(DatabaseException(
            "An internal server error occurred.",
            details={"original_error": str(e)}
        ))
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        from .exceptions import BaseException
        return create_error_response(BaseException(
            "An unexpected error occurred.",
            details={"error_type": type(e).__name__}
        ))
