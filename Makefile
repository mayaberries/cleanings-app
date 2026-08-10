#!/bin/bash

DOCKER_DB = fastapi-pets-db

help: ## Show this help message
	@echo 'usage: make [target]'
	@echo
	@echo 'targets:'
	@egrep '^(.+)\:\ ##\ (.+)' ${MAKEFILE_LIST} | column -t -c 2 -s ':#'

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

tests: ## Run tests locally (venv), against the dockerized db
	cd backend && pytest -v

pep: ## Run PEP8 style standards locally
	cd backend && autopep8 . --recursive --in-place --pep8-passes 2000 --verbose

freeze-deps: ## Freeze the active venv's installed packages into backend/requirements.txt
	cd backend && pip freeze | grep -v '^pip-chill' > requirements.txt

install-deps: ## Install backend/requirements.in into the active venv
	cd backend && pip install -r requirements.in

update-deps: ## Install requirements.in, then refreeze requirements.txt (run after adding a new dep)
	cd backend && pip install -r requirements.in && pip freeze | grep -v '^pip-chill' > requirements.txt