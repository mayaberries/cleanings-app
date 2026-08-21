#!/bin/bash

DOCKER_DB = fastapi-pets-db

help: ## Show this help message
	@echo 'usage: make [target]'
	@echo
	@echo 'targets:'
	@egrep '^(.+)\:\ ##\ (.+)' ${MAKEFILE_LIST} | column -t -c 2 -s ':#'

run: ## Start the FastAPI server locally (venv), against the dockerized db
	cd backend && uvicorn app.api.server:app --reload

admin-dev: ## Start the Astro SSR admin dashboard's dev server (frontend/admin)
	cd frontend/admin && npm run dev

db-up: ## Start the database container
	docker-compose up -d db

db-stop: ## Stop the database container
	docker-compose stop db

db-down: ## Stop and remove the database container + volume (destructive)
	docker-compose down -v

db-login: ## Log into the Postgres server
	docker-compose exec db psql -h localhost -U postgres --dbname=postgres

db-logs: ## Show database container logs
	docker-compose logs --follow db

upgrade-db: ## Run migrations against the dockerized db, use with precaution
	cd backend && alembic upgrade head

downgrade-db: ## Roll back migrations against the dockerized db, use with precaution
	cd backend && alembic downgrade base

test: test-be test-admin ## Run all test suites (backend + admin)

test-be: ## Run backend tests locally (venv), against the dockerized db
	cd backend && pytest -v

prepare-env: ## Copy docker-compose/env templates into place if missing
	cp -n docker-compose.yml.dist docker-compose.yml
	cp -n backend/.env.template backend/.env

test-be-docker: prepare-env ## Run backend tests fully dockerized (build + ephemeral db), used in CI
	docker compose --profile test run --rm backend

test-be-docker-down: ## Tear down the dockerized backend test stack
	docker compose down -v

test-admin-install: ## Install admin dependencies + Playwright browsers, used in CI
	cd frontend/admin && npm ci && npx playwright install --with-deps

test-admin: ## Run the admin dashboard's Playwright tests (frontend/admin)
	cd frontend/admin && npm test

pep: ## Run PEP8 style standards locally
	cd backend && autopep8 . --recursive --in-place --pep8-passes 2000 --verbose

freeze-deps: ## Freeze the active venv's installed packages into backend/requirements.txt
	cd backend && pip freeze | grep -v '^pip-chill' > requirements.txt

install-deps: ## Install backend/requirements.in into the active venv
	cd backend && pip install -r requirements.in

update-deps: ## Install requirements.in, then refreeze requirements.txt (run after adding a new dep)
	cd backend && pip install -r requirements.in && pip freeze | grep -v '^pip-chill' > requirements.txt