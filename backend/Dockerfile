FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for potential C extensions and sqlite3 CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p instance backups logs harmony_baselines

EXPOSE 5000

CMD ["gunicorn", "-w", "1", "--threads", "2", "-b", "0.0.0.0:5000", "app:create_app()"]
