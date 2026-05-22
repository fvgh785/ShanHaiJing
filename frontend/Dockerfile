# Stage 1: Build Vue 3 frontend
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy built static files
COPY --from=builder /app/dist /usr/share/nginx/html/

# Nginx configuration is mounted via docker-compose.yml volume:
#   ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
# For standalone use (without docker compose), a minimal default.conf is
# baked into the image below so nginx can at least serve static files.
RUN mkdir -p /etc/nginx/ssl && \
    printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / {\n    try_files $$uri $$uri/ /index.html;\n  }\n}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
