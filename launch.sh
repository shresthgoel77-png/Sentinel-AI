#!/bin/bash
echo "=========================================="
echo "    Starting Sentinel AI Full Stack       "
echo "=========================================="

echo "[1/4] Starting PostgreSQL & Redis via Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running."
    exit 1
fi

if [ -f "docker-compose.yml" ]; then
    docker compose up -d || docker-compose up -d
else
    echo "Warning: docker-compose.yml not found. Make sure DB/Redis are running."
fi

echo "Waiting for postgres health..."
sleep 5

echo "[2/4] Running Database Migrations..."
cd backend && {
    if [ -f "alembic.ini" ]; then
        venv/Scripts/alembic upgrade head || venv/bin/alembic upgrade head || echo "Migrations skipped or failed."
    else
        echo "No alembic migrations initialized."
    fi
    cd ..
}

echo "[3/4] Booting FastAPI Backend..."
cd backend && {
    venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
}

echo "[4/4] Booting React / Vite Frontend..."
npm run dev -- --port 5173 &
FRONTEND_PID=$!

echo "=========================================="
echo " Sentinel AI Stack is Live."
echo " UI: http://localhost:5173"
echo " API: http://localhost:8000"
echo "=========================================="
echo "Press Ctrl+C to stop services."

trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM
wait $BACKEND_PID $FRONTEND_PID
