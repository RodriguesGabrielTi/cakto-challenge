.PHONY: help install install-dev test test-unit lint format clean migrate docker-build docker-up docker-down docker-clean docker-purge docker-logs docker-seed dev seed

# Alvo padrão
help:
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "  === Instalação ==="
	@echo "  make install          - Instalar dependências de produção"
	@echo "  make install-dev      - Instalar todas as dependências (incluindo dev)"
	@echo ""
	@echo "  === Testes ==="
	@echo "  make test             - Rodar todos os testes com cobertura"
	@echo "  make test-unit        - Rodar apenas testes unitários"
	@echo ""
	@echo "  === Qualidade de Código ==="
	@echo "  make lint             - Rodar linters (ruff, black check)"
	@echo "  make format           - Formatar código com black e ruff"
	@echo "  make clean            - Limpar cache e arquivos temporários"
	@echo ""
	@echo "  === Banco de Dados ==="
	@echo "  make migrate          - Rodar migrations"
	@echo "  make seed             - Popular banco com dados de desenvolvimento"
	@echo ""
	@echo "  === Docker ==="
	@echo "  make docker-build     - Buildar imagem Docker"
	@echo "  make docker-up        - Subir todos os containers"
	@echo "  make docker-down      - Parar todos os containers"
	@echo "  make docker-logs      - Ver logs dos containers"
	@echo "  make docker-clean     - Parar containers (preserva volumes)"
	@echo "  make docker-purge     - Parar e remover volumes (destrutivo)"
	@echo ""
	@echo "  === Desenvolvimento ==="
	@echo "  make dev              - Workflow completo: format, lint, test"
	@echo "  make run              - Rodar servidor de desenvolvimento"

# Instalação
install:
	poetry install --only main

install-dev:
	poetry install

# Testes
test:
	poetry run pytest --cov=src --cov-report=term-missing

test-unit:
	poetry run pytest tests/ -v

# Qualidade de Código
lint:
	poetry run ruff check src/ tests/
	poetry run black --check src/ tests/

format:
	poetry run black src/ tests/
	poetry run ruff check src/ tests/ --fix

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

# Banco de Dados
migrate:
	poetry run python manage.py migrate

seed:
	poetry run python manage.py loaddata fixtures/dev_seed.json

docker-seed:
	docker-compose exec app python manage.py loaddata fixtures/dev_seed.json

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down --remove-orphans

docker-purge:
	docker-compose down -v --remove-orphans

# Servidor de desenvolvimento
run:
	poetry run python manage.py runserver

# Workflow de desenvolvimento
dev: format lint test
	@echo "Checks de desenvolvimento concluídos!"
