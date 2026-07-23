#!/usr/bin/env bash
# build.sh - Script de build pour Render

echo "🚀 Starting build process for Karamu..."

# Installer les dépendances
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate --noinput

echo "✅ Build completed successfully!"