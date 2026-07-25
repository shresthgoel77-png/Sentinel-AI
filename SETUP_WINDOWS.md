# Sentinel AI - Windows Setup & Launch Guide

Follow these instructions to safely launch the Sentinel AI Dashboard and FastAPI Backend on Windows 11.

---

## 1. Prerequisites

**Docker Desktop** is required to run the PostgreSQL database and Redis caching layer.
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop).
2. Open Docker Desktop and ensure it is running (Look for the whale icon in your system tray, bottom right corner of your Windows taskbar).
3. Open PowerShell and verify by running:
   ```powershell
   docker info
   ```
   *If this returns an error, Docker is not running.*

### Fallback (If Docker is not possible)
If Docker Desktop fails to initialize, you must run PostgreSQL and Redis manually:
- Install [PostgreSQL 16](https://www.postgresql.org/download/windows/) locally. Create a database named `sentinel`.
- Install Redis via [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install). Open a WSL Ubuntu terminal and run `sudo apt update && sudo apt install redis-server -y && redis-server`.
- Update your `.env` variables to match your local IP ports (default `localhost:5432` and `localhost:6379`).

---

## 2. Launching the System

We have created two distinct scripts to ensure safe initialization of both the Backend APIs and the Frontend interfaces.

### Step A: Boot the Database & Backend
Open a standard Windows **PowerShell** window in the `ai-shield` project directory and run:

```powershell
.\launch.ps1
```

**This script automatically does the following:**
1. Checks that Docker Desktop is actively running.
2. Boots Postgres and Redis containers in the background.
3. Waits for Postgres to become healthy.
4. Safely applies the latest Alembic SQL architectures.
5. Launches the Uvicorn FastAPI server safely on port 8000.

*If PostgreSQL or Redis fail to connect due to Docker failures, the backend will print a safe, clear error and abort rather than crashing silently.*

### Step B: Boot the Frontend Dashboard
Open a **second** Windows **PowerShell** window in the same `ai-shield` project folder and run:

```powershell
.\launch-frontend.ps1
```
This triggers the Vite React process. Open your browser to `http://localhost:5173`.

---

## 3. Verifying the Services

To guarantee your system is fully functional, run the following verification checks in a new PowerShell window:

**1. Check Docker Containers**
```powershell
docker ps
```
*You should explicitly see `sentinel-postgres` and `sentinel-redis` mapped securely to `:5432` and `:6379`.*

**2. Check Backend Health**
```powershell
curl http://localhost:8000/health
```
*(Optionally ping `http://localhost:8000/docs` to see the full Swagger spec)*

**3. Test Redis Connectivity**
```powershell
docker exec -it sentinel-redis redis-cli ping
```
*Expected Output: `PONG`*
