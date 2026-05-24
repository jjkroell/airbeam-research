#!/bin/bash
# This script runs on Jesse's server every time you push to GitHub
set -e

cd /home/sasha/site

echo "→ Pulling latest code..."
git pull origin main

echo "→ Rebuilding and restarting..."
docker compose down
docker compose up -d --build

echo "✓ AirBeam deployed!"
