import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from app.config import Config
from app.models import db

migrate = Migrate()


def setup_logging(app):
    log_dir = app.config["LOG_DIR"]
    os.makedirs(log_dir, exist_ok=True)

    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=app.config.get("LOG_RETENTION_DAYS", 30),
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)

    app.logger.info("ShanHaiJing backend starting")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)

    setup_logging(app)

    os.makedirs(app.config["INSTANCE_DIR"], exist_ok=True)
    os.makedirs(app.config["BACKUP_DIR"], exist_ok=True)
    os.makedirs(app.config["LOG_DIR"], exist_ok=True)

    from app.errors import register_error_handlers
    register_error_handlers(app)

    from app.api import register_blueprints
    register_blueprints(app)

    @app.route("/api/v1/health")
    def health():
        deepseek_status = "unknown"
        api_key = app.config.get("DEEPSEEK_API_KEY")
        if api_key:
            deepseek_status = "configured"
        else:
            deepseek_status = "unconfigured"
        return {
            "status": "ok",
            "deepseek": deepseek_status,
        }

    return app
