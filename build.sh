#!/usr/bin/env bash
# Build script for Render deployment

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

echo "Backend build completed successfully"