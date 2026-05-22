import os
from logging.config import fileConfig
from alembic import context
from app import create_app
from app.models import db

config = context.config

# fileConfig reads logging setup from alembic.ini; flask db may
# resolve the ini path differently, so check both common locations
_ini_path = config.config_file_name
if _ini_path and os.path.exists(_ini_path):
    fileConfig(_ini_path)
elif os.path.exists("alembic.ini"):
    fileConfig("alembic.ini")

app = create_app()
target_metadata = db.metadata


def run_migrations_offline():
    url = app.config['SQLALCHEMY_DATABASE_URI']
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with app.app_context():
        connectable = db.engine
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
