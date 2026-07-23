#!/usr/bin/env bash
# build.sh - Script de build pour Render

set -e

echo "🚀 Starting build process for Karamu..."

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗄️ Applying database migrations..."
python manage.py migrate --noinput

echo "✅ Build completed successfully!"