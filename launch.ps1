Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    Starting Sentinel AI Full Stack       " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "[1/4] Checking Docker Status..." -ForegroundColor Yellow
docker info >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Desktop is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

Write-Host "[2/4] Starting PostgreSQL & Redis via Docker..." -ForegroundColor Yellow
if (Test-Path "docker-compose.yml") {
    # Prefer modernized docker cli, fallback to docker-compose legacy
    docker compose up -d 2>$null
    if ($LASTEXITCODE -ne 0) {
        docker-compose up -d
    }
} else {
    Write-Host "Warning: docker-compose.yml not found. Make sure DB/Redis are running." -ForegroundColor Yellow
}

Write-Host "Waiting for database to initialize (healthcheck)..."
$max_attempts = 15
$attempt = 1
while ($attempt -le $max_attempts) {
    $status = docker inspect -f '{{.State.Health.Status}}' sentinel-postgres 2>$null
    if ($status -eq "healthy") {
        Write-Host "PostgreSQL is healthy!" -ForegroundColor Green
        break
    }
    Write-Host "Waiting for PostgreSQL... (Attempt $attempt/$max_attempts)"
    Start-Sleep -Seconds 2
    $attempt++
}

Write-Host "[3/4] Running Database Migrations..." -ForegroundColor Yellow
Set-Location backend 
if (Test-Path "alembic.ini") {
    .\venv\Scripts\alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Migrations skipped or failed." -ForegroundColor Red
    }
} else {
    Write-Host "No alembic migrations initialized." -ForegroundColor Yellow
}
Set-Location ..

Write-Host "[4/4] Booting FastAPI Backend..." -ForegroundColor Yellow
Set-Location backend 
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
