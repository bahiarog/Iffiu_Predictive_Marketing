#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# IFFIU — Deploy to Hostinger VPS
# Run: chmod +x deploy.sh && ./deploy.sh
# ═══════════════════════════════════════════════════════════════════════

set -e

echo "🚀 IFFIU Deployment Script"
echo "══════════════════════════"

# ─── Step 1: System Updates ──────────────────────────────────────────
echo ""
echo "📦 Step 1: Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin git certbot

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# ─── Step 2: Project Setup ───────────────────────────────────────────
echo ""
echo "📁 Step 2: Setting up project..."
cd /root/iffiu  # or wherever you cloned

# Copy env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env with your real values!"
    echo "   nano .env"
    echo ""
    echo "   Required:"
    echo "   - SECRET_KEY (run: openssl rand -hex 32)"
    echo "   - DB_PASSWORD"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo ""
    read -p "Press Enter after editing .env..."
fi

# ─── Step 3: Build & Start ──────────────────────────────────────────
echo ""
echo "🐳 Step 3: Building and starting containers..."
sudo docker compose up -d --build

# ─── Step 4: SSL Certificate ────────────────────────────────────────
echo ""
echo "🔒 Step 4: SSL Certificate"
echo "   After DNS is pointed to this server, run:"
echo "   sudo certbot certonly --standalone -d iffiu.com -d www.iffiu.com"
echo "   Then uncomment the HTTPS block in nginx/iffiu.conf"
echo "   And run: sudo docker compose restart nginx"

# ─── Step 5: Verify ─────────────────────────────────────────────────
echo ""
echo "✅ Deployment complete!"
echo ""
echo "   🌐 Landing Page:  http://iffiu.com"
echo "   🎯 Live Demo:     http://iffiu.com/demo"
echo "   📊 Dashboard:     http://iffiu.com/dashboard"
echo "   🔧 Health Check:  http://iffiu.com/health"
echo "   📚 API Docs:      http://iffiu.com/api/docs (debug mode only)"
echo ""
echo "   📋 Logs:  sudo docker compose logs -f app"
echo "   🔄 Restart: sudo docker compose restart"
echo "   🛑 Stop:    sudo docker compose down"
