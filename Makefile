# Pilah.in — Local Development Makefile
# Usage: make [target]
# Requires: Docker Desktop, Python 3.13+, Node.js 24+

.PHONY: help up down ps logs backend frontend migrate seed-admin test e2e clean

help:
	@echo "Pilah.in Local Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up            - Start Postgres + Redis + ML service (Docker)"
	@echo "  make down          - Stop all Docker services"
	@echo "  make ps            - Show running containers"
	@echo "  make logs          - Tail Docker logs"
	@echo ""
	@echo "Backend:"
	@echo "  make backend       - Install deps + migrate + run Django (port 8000)"
	@echo "  make migrate       - Run Django migrations"
	@echo "  make seed-admin    - Create admin GoGreen demo account"
	@echo "  make test          - Run Django test suite (TC-001..TC-053)"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend      - Install deps + run Vite dev (port 3000)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Stop containers + delete volumes (DATA LOST)"

# ------------------------------------------------------------------
# Infrastructure (Docker: Postgres, Redis, ML service)
# ------------------------------------------------------------------
up:
	@echo "Starting Pilah.in infrastructure..."
	docker compose -f FASE_0_Infrastructure/docker-compose.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	docker compose -f FASE_0_Infrastructure/docker-compose.yml ps

down:
	docker compose -f FASE_0_Infrastructure/docker-compose.yml down

ps:
	docker compose -f FASE_0_Infrastructure/docker-compose.yml ps

logs:
	docker compose -f FASE_0_Infrastructure/docker-compose.yml logs -f

# ------------------------------------------------------------------
# Backend (Django)
# ------------------------------------------------------------------
backend:
	@echo "Setting up backend..."
	pip install -r requirements.txt
	cp -n .env.example .env 2>/dev/null || true
	python manage.py migrate
	@echo ""
	@echo "Backend ready on http://localhost:8000"
	python manage.py runserver 0.0.0.0:8000

migrate:
	python manage.py migrate

seed-admin:
	python manage.py seed_demo
	@echo "Seed selesai. Admin: admin.gogreen@unpad.ac.id / AdminPass123!"

test:
	python manage.py test tests.test_tc_001_012_auth tests.test_tc_013_030_upload tests.test_tc_031_041_classification tests.test_tc_042_053_points --settings=config.settings_test --noinput

# ------------------------------------------------------------------
# Frontend (React + Vite)
# ------------------------------------------------------------------
frontend:
	@echo "Setting up frontend..."
	cd FASE_3_Frontend/pilah-frontend && npm install
	cd FASE_3_Frontend/pilah-frontend && cp -n .env.example .env 2>/dev/null || true
	@echo ""
	@echo "Frontend ready on http://localhost:3000"
	cd FASE_3_Frontend/pilah-frontend && npm run dev

# ------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------
clean:
	@echo "WARNING: This will delete all Docker volumes (data lost)."
	@read -p "Continue? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose -f FASE_0_Infrastructure/docker-compose.yml down -v; \
		echo "Cleanup completed"; \
	fi
