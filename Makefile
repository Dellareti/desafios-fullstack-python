.PHONY: install run test test-unit test-integration lint format docker-up docker-down

# -- Instalação
install:
	pip install -e ".[dev]"
	python -m playwright install chromium

# -- Desenvolvimento
run:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# -- Testes
test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v --timeout=60 -m integration

# -- Qualidade de código
lint:
	python -m ruff check app/ tests/
	python -m mypy app/

format:
	python -m black app/ tests/

# -- Docker
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down
