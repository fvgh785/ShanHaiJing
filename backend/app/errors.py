from flask import jsonify
from app.hermes_client.retry import CircuitBreakerOpen


def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": str(e.description) if hasattr(e, "description") else str(e),
            }
        }), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
            }
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "The method is not allowed for the requested URL.",
            }
        }), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred.",
            }
        }), 500
