#!/bin/bash
# run_local.sh
echo "\n============================================="
echo "   Sentinel AI Gateway - Local Stack Boot     "
echo "============================================="

# 1. Check for .env file
if [ -f ".env" ] || [ -f "backend/.env" ]; then
    echo "[✓] Environment variables found."
else
    echo "[!] Warning: No .env file found. Copying .env.example to .env..."
    cp .env.example .env
fi

# 2. Database Migrations
echo "\n--- [Running Database Migrations] ---"
cd backend
if [ -f "alembic.ini" ]; then
    venv/Scripts/alembic upgrade head || echo "[!] Alembic migrations paused or unconfigured."
else
    echo "[!] No alembic.ini found."
fi

# 3. Boot FastAPI Backend
echo "\n--- [Booting Sentinel FastAPI Gateway] ---"
# Using the local project interpreter securely
venv/Scripts/python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# 4. Boot React Vite Frontend
echo "\n--- [Booting Sentinel React Console] ---"
npm run dev &
FRONTEND_PID=$!

echo "\n============================================="
echo " Sentinel AI Gateway is Live!"
echo " UI Endpoint : http://localhost:5173"
echo " API Gateway : http://localhost:8000/v1"
echo "============================================="
echo "Press Ctrl+C to terminate the local cluster."

# Clean up processes on exit
trap "echo '\nShutting down cluster...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM
wait $BACKEND_PID $FRONTEND_PID
