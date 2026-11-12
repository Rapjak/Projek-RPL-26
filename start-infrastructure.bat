@echo off
REM ============================================================
REM Pilah.in Infrastructure Startup Script (Windows)
REM Menjalankan PostgreSQL, Redis, dan ML service via Docker.
REM ============================================================

echo ========================================
echo Pilah.in Infrastructure Startup
echo ========================================
echo.

REM Cek Docker terinstall
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker tidak terinstall.
    echo Install Docker Desktop dari https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Cek Docker berjalan
docker info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker belum berjalan.
    echo Buka Docker Desktop lalu coba lagi.
    pause
    exit /b 1
)

echo [1/3] Menyiapkan file .env...
if not exist .env (
    echo Membuat .env dari .env.example...
    copy .env.example .env >nul
    echo SELESAI. .env dibuat dengan nilai default dev.
)

echo.
echo [2/3] Menjalankan infrastruktur (Postgres, Redis, ML service)...
cd FASE_0_Infrastructure
docker compose up -d

echo.
echo [3/3] Menunggu service sehat...
timeout /t 10 /nobreak >nul
docker compose ps

echo.
echo ========================================
echo Infrastruktur Berjalan!
echo ========================================
echo.
echo Services:
echo   PostgreSQL : localhost:5432  (db: pilah_in, user: postgres)
echo   Redis      : localhost:6379
echo   ML Service : http://localhost:8001/health
echo.
echo Langkah selanjutnya:
echo   1. Backend  : python manage.py migrate ^&^& python manage.py runserver 0.0.0.0:8000
echo   2. Buat admin: make seed-admin  (atau lihat README)
echo   3. Frontend : cd FASE_3_Frontend\pilah-frontend ^&^& npm install ^&^& npm run dev
echo.
echo Untuk stop: docker compose -f FASE_0_Infrastructure\docker-compose.yml down
echo.
pause
