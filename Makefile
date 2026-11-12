# Makefile for Pilah.in Local Development
# Usage: make [target]

.PHONY: help up down logs ps shell-django shell-postgres shell-redis test clean

help:
	@echo "Pilah.in Local Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up              - Start all services (postgres, redis, minio)"
	@echo "  make down            - Stop all services"
	@echo "  make ps              - Show running containers"
	@echo "  make logs            - View logs (all services)"
	@echo "  make clean           - Remove volumes and stop services"
	@echo ""
	@echo "Database:"
	@echo "  make shell-postgres  - Connect to PostgreSQL shell"
	@echo "  make db-migrate      - Run Django migrations"
	@echo "  make db-backup       - Backup PostgreSQL database"
	@echo ""
	@echo "Cache:"
	@echo "  make shell-redis     - Connect to Redis shell"
	@echo "  make redis-flush     - Clear Redis cache (dev only)"
	@echo ""
	@echo "Storage:"
	@echo "  make minio-console   - Open MinIO console in browser"
	@echo "  make minio-test      - Test MinIO bucket access"
	@echo ""
	@echo "Backend:"
	@echo "  make shell-django    - Connect to Django shell"
	@echo "  make run-django      - Run Django development server"
	@echo "  make test            - Run tests"
	@echo ""

# Infrastructure Commands
up:
	@echo "Starting Pilah.in infrastructure..."
	docker-compose -f FASE_0_Infrastructure/docker-compose.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker-compose -f FASE_0_Infrastructure/docker-compose.yml ps

down:
	@echo "Stopping all services..."
	docker-compose -f FASE_0_Infrastructure/docker-compose.yml down

ps:
	docker-compose -f FASE_0_Infrastructure/docker-compose.yml ps

logs:
	docker-compose -f FASE_0_Infrastructure/docker-compose.yml logs -f

# Database Commands
shell-postgres:
	docker exec -it pilah_postgres psql -U ${DATABASE_USER:-postgres} -d ${DATABASE_NAME:-pilah_in}

db-migrate:
	docker exec pilah_postgres psql -U ${DATABASE_USER:-postgres} -d ${DATABASE_NAME:-pilah_in} -f /docker-entrypoint-initdb.d/01_schema.sql

db-backup:
	@echo "Backing up PostgreSQL database..."
	docker exec pilah_postgres pg_dump -U ${DATABASE_USER:-postgres} ${DATABASE_NAME:-pilah_in} > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup completed: backup_$(shell date +%Y%m%d_%H%M%S).sql"

# Redis Commands
shell-redis:
	docker exec -it pilah_redis redis-cli

redis-flush:
	@echo "WARNING: Clearing all Redis cache (development only)"
	docker exec pilah_redis redis-cli FLUSHALL

# MinIO Commands
minio-console:
	@echo "Opening MinIO Console at http://localhost:9001"
	@echo "Username: ${MINIO_ROOT_USER:-pilah_admin}"
	@echo "Password: ${MINIO_ROOT_PASSWORD:-pilah_minio_password_dev}"
	open http://localhost:9001 || xdg-open http://localhost:9001 || start http://localhost:9001

minio-test:
	@echo "Testing MinIO connection..."
	docker exec pilah_minio mc ls pilah

# Status Check
status:
	@echo "=== Pilah.in Infrastructure Status ==="
	@echo ""
	@echo "PostgreSQL:"
	@docker exec pilah_postgres pg_isready -U ${DATABASE_USER:-postgres} || echo "NOT RUNNING"
	@echo ""
	@echo "Redis:"
	@docker exec pilah_redis redis-cli ping || echo "NOT RUNNING"
	@echo ""
	@echo "MinIO:"
	@docker exec pilah_minio curl -s http://localhost:9000/minio/health/live > /dev/null && echo "RUNNING" || echo "NOT RUNNING"

# Cleanup
clean:
	@echo "WARNING: This will delete all volumes and data"
	@read -p "Continue? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f FASE_0_Infrastructure/docker-compose.yml down -v; \
		echo "Cleanup completed"; \
	fi
