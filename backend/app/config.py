import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(os.path.dirname(BASE_DIR), 'instance')

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(INSTANCE_DIR, "app.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

    HERMES_BASE_URL = os.environ.get('HERMES_BASE_URL', 'http://hermes:8000')
    HERMES_TIMEOUT = int(os.environ.get('HERMES_TIMEOUT', '30'))
    HERMES_MAX_RETRIES = int(os.environ.get('HERMES_MAX_RETRIES', '3'))
    HERMES_CIRCUIT_BREAK_THRESHOLD = int(os.environ.get('HERMES_CIRCUIT_BREAK_THRESHOLD', '5'))
    HERMES_CIRCUIT_BREAK_COOLDOWN = int(os.environ.get('HERMES_CIRCUIT_BREAK_COOLDOWN', '60'))

    BACKUP_DIR = os.environ.get(
        'BACKUP_DIR',
        os.path.join(os.path.dirname(BASE_DIR), 'backups')
    )
    HARMONY_DIR = os.environ.get(
        'HARMONY_DIR',
        os.path.join(os.path.dirname(BASE_DIR), 'harmony_baselines')
    )

    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', str(16 * 1024 * 1024)))  # 16MB

    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', os.path.join(os.path.dirname(BASE_DIR), 'logs'))
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', '30'))
