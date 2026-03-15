ROOT_DIR := $(CURDIR)
APP_HOST ?= 0.0.0.0
APP_PORT ?= 8080
APP_CONFIG_FILE ?= $(ROOT_DIR)/config/local.yaml

.PHONY: test test-backend fmt-backend run-backend run-backend-local print-config docker-build docker-up docker-down

test: test-backend

test-backend:
	cd backend && .venv/bin/python -m pytest

fmt-backend:
	cd backend && .venv/bin/python -m compileall app tests

run-backend:
	APP_CONFIG_FILE="$(APP_CONFIG_FILE)" APP_PORT="$(APP_PORT)" PYTHONPATH="$(ROOT_DIR)/backend" backend/.venv/bin/python -m uvicorn app.main:app --host $(APP_HOST) --port $(APP_PORT)

run-backend-local:
	APP_CONFIG_FILE="$(APP_CONFIG_FILE)" APP_PORT="$(APP_PORT)" PYTHONPATH="$(ROOT_DIR)/backend" backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port $(APP_PORT)

print-config:
	@echo APP_CONFIG_FILE=$(APP_CONFIG_FILE)
	@echo APP_HOST=$(APP_HOST)
	@echo APP_PORT=$(APP_PORT)

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
