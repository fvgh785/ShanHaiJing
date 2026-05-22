FROM python:3.11-slim

RUN pip install --no-cache-dir hermes-agent

WORKDIR /app

# Create Hermes data directories
RUN mkdir -p /root/.hermes/skills /root/.hermes/memory

# Copy custom skill files
COPY skills/ /root/.hermes/skills/

EXPOSE 8000

CMD ["hermes", "serve", "--host", "0.0.0.0", "--port", "8000", "--low-memory"]
