# Cakto Challenge - Mini Split Engine + Ledger + Outbox

Teste prático Backend Sênior para a Cakto. API de pagamentos com cálculo de taxas, split de recebíveis, ledger contábil, idempotência e padrão Transactional Outbox.

## Stack

- Python 3.11 + Django 5.2 + Django REST Framework
- PostgreSQL 15 (via Docker) / SQLite (fallback local)
- Poetry (gerenciamento de dependências)
- django-injector (injeção de dependência)
- Pytest (testes)
- Ruff + Black (linting e formatação)
- Docker + Docker Compose

## Como rodar

### Pré-requisitos

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- Docker e Docker Compose (opcional, para PostgreSQL)

### Setup local (SQLite)

```bash
make install-dev
make migrate
make run
```

### Setup com Docker (PostgreSQL)

```bash
cp .env.example .env
make docker-up
make docker-logs
```

### Testes e qualidade

```bash
make test       # testes com cobertura
make lint       # ruff + black check
make format     # formatar código
```

### Postman

Coleção disponível em `postman/cakto-challenge.postman_collection.json` para importar no Postman. Inclui cenários de pagamento, idempotência e validação com scripts de teste.

## Estrutura do projeto

```
src/
  common/              # Base compartilhada
    models.py          # BaseModel (UUID v4)
    constants.py       # Precisão decimal, multiplicadores
    exceptions.py      # Exceções de domínio (BusinessValidationError, ConflictError)
    middleware.py       # Tradução exceção de domínio -> HTTP
  billing/             # Core Domain
    constants.py       # Constantes de negócio (taxas, limites, moedas)
    models.py          # Payment, LedgerEntry
    rates.py           # PlatformRates, CardRates (configuração injetável)
    di.py              # Módulo de injeção de dependência
    services/          # Lógica de negócio pura
      fee_calculator.py
      split_calculator.py
      payment_service.py
    repositories/      # Acesso a dados
      payment_repository.py
    api/               # Camada HTTP (DRF) - apenas validação de estrutura
      serializers.py
      views.py
      urls.py
  idempotency/         # Controle de idempotência
    models.py          # IdempotencyRecord
    repositories.py
    services.py        # Verificação SHA-256 + cache de resposta
  outbox/              # Transactional Outbox
    models.py          # OutboxEvent
    repositories/
      outbox_repository.py
tests/                 # 36 testes (unitários + integração)
postman/               # Coleção Postman
scripts/               # Entrypoint Docker
```

## Decisões técnicas

### 1. Precisão financeira e arredondamento

Toda aritmética financeira usa `Decimal` inicializado a partir de strings (`Decimal("0.01")`), nunca `float`. Arredondamento com `ROUND_HALF_UP` para 2 casas decimais, consistente com o padrão bancário brasileiro.

A constante `DECIMAL_PRECISION = Decimal("0.01")` centraliza a precisão e é usada em todos os cálculos via `quantize()`.

### 2. Regra de centavos (Largest Remainder Method)

O split de recebíveis usa o Largest Remainder Method para garantir que a soma dos valores distribuídos seja **exatamente** igual ao `net_amount`, sem sobra ou falta de centavos.

O algoritmo:
1. Converte o `net_amount` para centavos (inteiro) para evitar erros de arredondamento
2. Calcula o valor base de cada recebedor (`floor` do percentual aplicado)
3. Distribui os centavos restantes para os recebedores com maior parte fracionária
4. Converte de volta para `Decimal` com 2 casas

Isso garante a invariante `sum(receivables) == net_amount` em todos os casos, incluindo splits como 33.33/33.33/33.34.

### 3. Estratégia de idempotência

A idempotência é implementada com:

- **SHA-256 do payload**: hash determinístico (JSON com `sort_keys=True`) identifica univocamente cada requisição
- **`SELECT FOR UPDATE`**: lock pessimista no registro de idempotência previne race conditions entre requisições concorrentes
- **Transação ACID única**: a verificação de idempotência, criação do pagamento, ledger entries, outbox event e cache da resposta acontecem dentro do mesmo `transaction.atomic()`

Fluxos:
- Chave nova: processa normalmente, salva resposta no cache
- Chave existente + mesmo hash: retorna resposta cacheada (201)
- Chave existente + hash diferente: rejeita com 409 Conflict

### 4. Arquitetura em camadas

O projeto segue uma separação clara de responsabilidades:

- **Services**: lógica de negócio pura, sem dependência de Django/HTTP. Podem ser reutilizados em qualquer interface (REST, gRPC, CLI)
- **Repositories**: encapsulam acesso a dados (queries, creates). Única camada que conhece os models Django
- **Serializers/Views**: camada HTTP fina, apenas validação de estrutura e delegação para os services
- **Middleware**: traduz exceções de domínio (`ConflictError` -> 409, `BusinessValidationError` -> 400) sem acoplar services ao HTTP
- **Injeção de dependência**: via `django-injector`, todas as dependências são injetadas nos construtores. Taxas (`PlatformRates`) são configuráveis e injetáveis

### 5. Métricas que colocaria em produção

- **Latência p50/p95/p99** do endpoint `/api/v1/payments`
- **Taxa de erro** por tipo (400, 409, 500) com alertas em thresholds
- **Hit rate de idempotência** (cache vs processamento novo)
- **Tempo de lock** no `SELECT FOR UPDATE` (indicador de contenção)
- **Outbox lag**: diferença entre `created_at` e `published_at` dos eventos (monitorar atraso na publicação)
- **Volume transacionado** (gross_amount agregado por período)
- **Distribuição de métodos** de pagamento (PIX vs CARD) e parcelas

### 6. Se tivesse mais tempo

- **Tipar dicts com dataclasses**: os services usam `dict` para entrada/saída. Criar dataclasses tipadas (`PaymentInput`, `PaymentResult`, `Receivable`) para contratos explícitos
- **Outbox publisher**: worker que consome eventos pendentes e publica em um broker (RabbitMQ/Kafka), com retry e dead letter queue
- **Endpoint GET**: consulta de pagamento por ID com ledger entries
- **Endpoint POST /checkout/quote**: cálculo de taxas sem persistir (já existe o método `calculate()` no service)
- **Cache de taxas**: mover `PlatformRates` para base de dados com cache Redis, permitindo alteração sem deploy
- **Rate limiting**: proteção contra abuso no endpoint
- **Observabilidade**: OpenTelemetry com traces distribuídos, structured logging com correlation ID
- **Paginação e filtros**: no futuro endpoint de listagem
- **CI/CD completo**: deploy automatizado, migrations em pipeline separado

## Uso de IA

Este projeto foi desenvolvido com auxílio do Claude Code (Anthropic) para estruturação, geração de testes e revisão da lógica financeira. Todo código foi revisado e validado manualmente.
