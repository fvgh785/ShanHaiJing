#!/bin/bash
#
# setup-ssl.sh - Let's Encrypt SSL Certificate Initial Setup for ShanHaiJing
#
# This script bootstraps SSL for the first deployment.
# It generates a self-signed placeholder certificate so nginx can start,
# then guides you through requesting a real Let's Encrypt certificate.
#
# Prerequisites:
#   - Docker and Docker Compose installed
#   - Domain name pointing to this server's public IP
#   - Ports 80 and 443 open in firewall/security group
#
# Target OS: Alibaba Cloud Linux 3 (RHEL-based)
#
# Usage:
#   bash scripts/setup-ssl.sh your-domain.com
#

set -euo pipefail

# ============================================================
# Configuration
# ============================================================

DOMAIN="${1:-}"
EMAIL="${2:-admin@${DOMAIN}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CERTBOT_WEBROOT="${PROJECT_DIR}/certbot/www"
CERTBOT_CERTS="${PROJECT_DIR}/certbot/certs"
NGINX_SSL_DIR="${PROJECT_DIR}/nginx/ssl"

# ============================================================
# Color output helpers
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}[STEP]${NC} $*"; }

# ============================================================
# Validate arguments
# ============================================================

if [ -z "$DOMAIN" ]; then
    log_error "Usage: bash scripts/setup-ssl.sh <domain> [email]"
    log_error "Example: bash scripts/setup-ssl.sh shanhaijing.example.com admin@example.com"
    exit 1
fi

log_info "Setting up SSL for domain: ${DOMAIN}"
log_info "Notification email: ${EMAIL}"

# Check if running as root (certbot may need it for binding port 80)
if [ "$(id -u)" -ne 0 ]; then
    log_warn "This script is not running as root. Some operations may require sudo."
fi

# ============================================================
# Step 1: Generate self-signed placeholder certificate
# ============================================================

log_step "Step 1/5: Generating self-signed placeholder certificate..."

mkdir -p "$NGINX_SSL_DIR"

# Check if placeholder certs already exist
if [ -f "${NGINX_SSL_DIR}/fullchain.pem" ] && [ -f "${NGINX_SSL_DIR}/privkey.pem" ]; then
    log_warn "Placeholder certificates already exist at ${NGINX_SSL_DIR}/"
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping placeholder certificate generation."
    else
        rm -f "${NGINX_SSL_DIR}/fullchain.pem" "${NGINX_SSL_DIR}/privkey.pem"
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "${NGINX_SSL_DIR}/privkey.pem" \
            -out "${NGINX_SSL_DIR}/fullchain.pem" \
            -subj "/CN=localhost" \
            -addext "subjectAltName=DNS:localhost,DNS:${DOMAIN}"
        log_info "Self-signed placeholder certificate generated."
    fi
else
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${NGINX_SSL_DIR}/privkey.pem" \
        -out "${NGINX_SSL_DIR}/fullchain.pem" \
        -subj "/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,DNS:${DOMAIN}"
    log_info "Self-signed placeholder certificate generated at ${NGINX_SSL_DIR}/"
fi

# ============================================================
# Step 2: Verify Docker Compose services can start
# ============================================================

log_step "Step 2/5: Testing nginx startup with placeholder certificate..."

cd "$PROJECT_DIR"

if docker compose ps nginx 2>/dev/null | grep -q "Up"; then
    log_info "Nginx is already running. Restarting to pick up certificate changes..."
    docker compose restart nginx
else
    log_info "Starting nginx with placeholder certificate..."
    docker compose up -d nginx
fi

sleep 2

if docker compose ps nginx 2>/dev/null | grep -q "Up"; then
    log_info "Nginx started successfully with placeholder certificate."
else
    log_error "Nginx failed to start. Check logs: docker compose logs nginx"
    exit 1
fi

# ============================================================
# Step 3: Verify HTTP accessibility
# ============================================================

log_step "Step 3/5: Verifying HTTP accessibility..."

# Test that port 80 is accessible (required for ACME challenge)
if curl -s -o /dev/null -w "%{http_code}" "http://${DOMAIN}/.well-known/acme-challenge/" 2>/dev/null | grep -q "40[0-4]"; then
    log_info "HTTP port 80 is accessible (returned expected 404 for empty ACME path)."
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${DOMAIN}/" 2>/dev/null || echo "failed")
    if [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "200" ]; then
        log_info "HTTP port 80 is accessible (returned ${HTTP_CODE})."
    else
        log_error "Cannot reach HTTP port 80 on ${DOMAIN}. HTTP code: ${HTTP_CODE}"
        log_error "Please verify:"
        log_error "  1. Domain DNS A record points to this server"
        log_error "  2. Firewall/security group allows port 80"
        log_error "  3. Nginx is running: docker compose ps nginx"
        log_error "  4. Try: docker compose logs nginx"
        exit 1
    fi
fi

# ============================================================
# Step 4: Request Let's Encrypt certificate via certbot
# ============================================================

log_step "Step 4/5: Requesting Let's Encrypt certificate..."

# Check if certbot is available
if command -v certbot &> /dev/null; then
    log_info "certbot found. Using local installation."
    CERTBOT_CMD="certbot"
elif command -v docker &> /dev/null; then
    log_info "Using certbot via Docker (no local installation found)."

    CERTBOT_CMD="docker run --rm \
        -v ${CERTBOT_CERTS}:/etc/letsencrypt \
        -v ${CERTBOT_WEBROOT}:/var/www/certbot \
        certbot/certbot"
else
    log_error "Neither certbot nor Docker found. Cannot request certificate."
    log_info "Manual steps (Alibaba Cloud Linux 3):"
    log_info "  1. yum install -y certbot"
    log_info "  2. Then re-run: bash scripts/setup-ssl.sh ${DOMAIN} ${EMAIL}"
    exit 1
fi

# Create certbot directories
mkdir -p "$CERTBOT_CERTS" "$CERTBOT_WEBROOT"

log_info "Running certbot in standalone/webroot mode..."
log_info "This may take a minute. You will see progress output below:"
echo ""

$CERTBOT_CMD certonly \
    --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal

CERTBOT_EXIT=$?

if [ $CERTBOT_EXIT -ne 0 ]; then
    log_error "certbot failed with exit code ${CERTBOT_EXIT}."
    log_info "Common issues:"
    log_info "  1. DNS not propagated (wait 5-30 minutes)"
    log_info "  2. Port 80 blocked by firewall"
    log_info "  3. Rate limited (wait 1 hour for retry)"
    log_info "After resolving, re-run: bash scripts/setup-ssl.sh ${DOMAIN} ${EMAIL}"
    exit 1
fi

log_info "Let's Encrypt certificate obtained successfully!"

# ============================================================
# Step 5: Link certificates and reload nginx
# ============================================================

log_step "Step 5/5: Linking certificates and reloading nginx..."

# Copy actual certs to nginx SSL directory
CERT_LIVE="/etc/letsencrypt/live/${DOMAIN}"

if [ -d "$CERT_LIVE" ]; then
    log_info "Copying certificates from ${CERT_LIVE}/ to ${NGINX_SSL_DIR}/"
    cp "${CERT_LIVE}/fullchain.pem" "${NGINX_SSL_DIR}/fullchain.pem"
    cp "${CERT_LIVE}/privkey.pem" "${NGINX_SSL_DIR}/privkey.pem"
elif [ -d "${CERTBOT_CERTS}/live/${DOMAIN}" ]; then
    log_info "Copying certificates from certbot volume to ${NGINX_SSL_DIR}/"
    cp "${CERTBOT_CERTS}/live/${DOMAIN}/fullchain.pem" "${NGINX_SSL_DIR}/fullchain.pem"
    cp "${CERTBOT_CERTS}/live/${DOMAIN}/privkey.pem" "${NGINX_SSL_DIR}/privkey.pem"
else
    log_warn "Certificate directory not found. Check certbot output."
    log_info "You may need to manually copy certs to ${NGINX_SSL_DIR}/"
    exit 1
fi

log_info "Reloading nginx to use new certificate..."
cd "$PROJECT_DIR"
docker compose exec nginx nginx -s reload 2>/dev/null || docker compose restart nginx

log_info ""
log_info "=========================================="
log_info "  SSL setup complete for ${DOMAIN}!"
log_info "=========================================="
log_info ""
log_info "Certificate location: ${NGINX_SSL_DIR}/"
log_info "  - fullchain.pem (public certificate + chain)"
log_info "  - privkey.pem   (private key)"
log_info ""
log_info "Visit: https://${DOMAIN}/"
log_info ""

# ============================================================
# Renewal hint
# ============================================================

log_info "Auto-renewal setup (recommended):"
log_info ""
log_info "Add this cron job to auto-renew every 60 days:"
log_info "  crontab -e"
log_info "  # m h  dom mon dow   command"
log_info "  0 2 1 * * certbot renew --quiet --post-hook 'docker compose -f ${PROJECT_DIR}/docker-compose.yml exec nginx nginx -s reload'"
log_info ""
log_info "Or test renewal manually:"
log_info "  certbot renew --dry-run"

exit 0
