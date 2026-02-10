# Cakto Challenge — Mini Split Engine + Ledger + Outbox

Teste prático Backend Sênior para a Cakto. API de pagamentos com cálculo de taxas, split de recebíveis, ledger contábil, idempotência e padrão Transactional Outbox.

## Stack

- Python 3.11 + Django 5.2 + Django REST Framework
- PostgreSQL 15 (via Docker) / SQLite (fallback local)
- Poetry (gerenciamento de dependências)
- Pytest + Factory Boy (testes)
- Ruff + Black (linting e formatação)
- Docker + Docker Compose

## Como rodar

### Pré-requisitos

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- Docker e Docker Compose (opcional, para PostgreSQL)

### Setup local (SQLite)

```bash
# Instalar dependências
make install-dev

# Rodar migrations
make migrate

# Iniciar servidor
make run
```

### Setup com Docker (PostgreSQL)

```bash
# Copiar variáveis de ambiente
cp .env.example .env

# Subir containers (app + PostgreSQL)
make docker-up

# Ver logs
make docker-logs
```

### Testes

```bash
# Rodar todos os testes com cobertura
make test

# Apenas testes unitários
make test-unit
```

### Qualidade de código

```bash
# Formatar código
make format

# Rodar linters
make lint

# Workflow completo (format + lint + test)
make dev
```

## Estrutura do projeto

```
src/
  common/          # Utilitários compartilhados (Decimal helpers, Abstract Models)
  billing/         # Core Domain — Pagamentos
    models.py      # Payment, LedgerEntry
    services.py    # Lógica de negócio (cálculo de taxas, split)
    selectors.py   # Queries de leitura
    api/           # Camada HTTP (DRF)
      serializers.py
      views.py
      urls.py
  idempotency/     # Controle de idempotência (Middleware + Model)
  outbox/          # Transactional Outbox (Model + evento payment_captured)
tests/             # Testes automatizados
scripts/           # Entrypoint Docker, seed
```

## Uso de IA

Este projeto foi desenvolvido com auxílio do Claude Code (Anthropic) para:
- Estruturação do projeto e boilerplate
- Geração de testes e validação de edge cases
- Revisão da lógica financeira (arredondamento, distribuição de centavos)

Todo código gerado foi revisado e validado manualmente.

---

> **Seção de decisões técnicas será adicionada ao final do desenvolvimento.**
