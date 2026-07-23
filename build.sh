#!/usr/bin/env bash
# build.sh - Script de build pour Render

set -e

echo "🚀 Starting build process for Karamu..."

# Installer les dépendances système pour Pillow
echo "📦 Installing system dependencies for Pillow..."
apt-get update
apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    zlib1g-dev \
    libwebp-dev \
    libtiff-dev

# Installer les dépendances Python
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Collecter les fichiers statiques
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Appliquer les migrations
echo "🗄️ Applying database migrations..."
python manage.py migrate --noinput

echo "✅ Build completed successfully!"