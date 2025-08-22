#!/usr/bin/env bash
# Start script for Render deployment

# Start the FastAPI application with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}