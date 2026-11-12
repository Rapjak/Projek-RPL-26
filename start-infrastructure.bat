@echo off
REM Pilah.in Infrastructure Startup Script
REM Windows batch file for starting local development environment

echo ========================================
echo Pilah.in Infrastructure Startup
echo ========================================
echo.

REM Check Docker installed
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker not installed
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check Docker running
docker info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

echo [1/4] Checking environment configuration...
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env file with your local configuration
    echo Press any key to continue after editing .env
    pause
)

echo [2/4] Starting infrastructure services...
cd FASE_0_Infrastructure
docker-compose up -d

echo.
echo [3/4] Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

echo.
echo [4/4] Checking service status...
docker-compose ps

echo.
echo ========================================
echo Infrastructure Started Successfully!
echo ========================================
echo.
echo Services:
echo   PostgreSQL: localhost:5432
echo   Redis: localhost:6379
echo   MinIO API: localhost:9000
echo   MinIO Console: http://localhost:9001
echo.
echo Next steps:
echo   1. Access MinIO Console: http://localhost:9001
echo      Username: pilah_admin
echo      Password: pilah_minio_password_dev
echo.
echo   2. Connect to PostgreSQL:
echo      Host: localhost:5432
echo      Database: pilah_in
echo      User: postgres
echo.
echo   3. Test Redis:
echo      docker exec -it pilah_redis redis-cli ping
echo.
echo To stop services: docker-compose down
echo.
pause
