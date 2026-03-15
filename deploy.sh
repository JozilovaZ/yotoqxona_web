#!/bin/bash
set -e

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Stopping containers ==="
docker compose down

echo "=== Removing old static volume ==="
docker volume rm yotoqxona_web_static_files 2>/dev/null || true

echo "=== Building and starting containers ==="
docker compose up -d --build

echo "=== Deploy complete ==="
docker compose ps
