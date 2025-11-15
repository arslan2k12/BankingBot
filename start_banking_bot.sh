#!/bin/bash
cd "$(dirname "$0")"
source venv_bankbot/bin/activate
echo "🏦 Starting Banking Bot API Server..."
echo "📍 API Documentation: http://localhost:2024/docs"
echo "🔍 Health Check: http://localhost:2024/health"
echo "Press Ctrl+C to stop the server"
echo ""
uvicorn src.app.main:app --host 0.0.0.0 --port 2024 --reload
