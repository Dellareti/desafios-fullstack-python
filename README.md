# Transparência RPA

Robô de automação web para consulta de pessoas físicas no [Portal da Transparência do Governo Federal](https://portaldatransparencia.gov.br), exposto via API REST documentada.

## Funcionalidades

- Consulta por **CPF**, **NIS** ou **Nome**
- Coleta dados de **benefícios sociais** (Bolsa Família, Auxílio Brasil, Auxílio Emergencial, etc.)
- **Screenshot** da página capturada em Base64 no JSON de resposta
- Filtro opcional por beneficiários de programas sociais
- Execuções **simultâneas** sem conflito (sem estado global)
- Documentação automática via **Swagger/OpenAPI**

---

## Pré-requisitos

- Python 3.11+
- [Playwright](https://playwright.dev/python/) com Chromium

Ou:

- Docker + Docker Compose

---

## Instalação local

```bash
# 1. Clonar o repositório
git clone <url-do-repo> && cd desafios-fullstack-python

# 2. Instalar dependências + Chromium (via Makefile)
make install

# Ou manualmente:
pip install -e ".[dev]"
python -m playwright install chromium

# Atenção: pip instala scripts em um diretório que pode não estar no PATH.
# Use sempre python -m <ferramenta> para evitar "command not found":
#   python -m uvicorn  (não: uvicorn)
#   python -m pytest   (não: pytest)
#   python -m black    (não: black)

# 3. Configurar variáveis de ambiente
cp .env.example .env
```

## Rodando localmente

> **Atenção:** `uvicorn` é instalado dentro do ambiente Python e pode não estar no PATH do sistema.
> Use sempre `python -m uvicorn` ou o Makefile.

```bash
# Via Makefile (recomendado)
make run

# Ou diretamente
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API disponível em `http://localhost:8000`
Documentação em `http://localhost:8000/docs`

---

## Makefile — comandos disponíveis

```bash
make install          # Instala dependências e Chromium
make run              # Sobe a API em modo desenvolvimento
make test             # Todos os testes
make test-unit        # Testes unitários (sem internet, ~0.2s)
make test-integration # Testes de integração (acessa o portal, ~35s)
make lint             # ruff + mypy
make format           # black
make docker-up        # Build e sobe via Docker Compose
make docker-down      # Para os containers
```

---

## Rodando via Docker

```bash
# Build e iniciar
docker-compose up --build

# Em segundo plano
docker-compose up -d --build

# Parar
docker-compose down
```

---

## Testes

```bash
# Via Makefile
make test-unit
make test-integration

# Diretamente (usar sempre python -m para evitar problemas de PATH)
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v --timeout=60 -m integration
python -m pytest tests/ -v
```

---

## Exemplos de uso

### Consultar por CPF

```bash
curl -X POST http://localhost:8000/api/v1/consulta \
  -H "Content-Type: application/json" \
  -d '{
    "identificador": "123.456.789-00",
    "tipo": "CPF",
    "filtro_social": false
  }'
```

### Consultar por Nome

```bash
curl -X POST http://localhost:8000/api/v1/consulta \
  -H "Content-Type: application/json" \
  -d '{
    "identificador": "João da Silva",
    "tipo": "NOME",
    "filtro_social": false
  }'
```

### Consultar por Nome com filtro social

```bash
curl -X POST http://localhost:8000/api/v1/consulta \
  -H "Content-Type: application/json" \
  -d '{
    "identificador": "Silva",
    "tipo": "NOME",
    "filtro_social": true
  }'
```

### Consultar por NIS

```bash
curl -X POST http://localhost:8000/api/v1/consulta \
  -H "Content-Type: application/json" \
  -d '{
    "identificador": "12345678901",
    "tipo": "NIS"
  }'
```

### Health check

```bash
curl http://localhost:8000/api/v1/health
```

---

## Resposta de exemplo

```json
{
  "sucesso": true,
  "mensagem_erro": null,
  "nome": "LULA BLAUTH DA SILVA",
  "cpf": "***.038.380-**",
  "nis": null,
  "data_nascimento": null,
  "municipio_uf": "CAXIAS DO SUL - RS",
  "beneficios": [
    {
      "nome_beneficio": "Auxílio Emergencial",
      "competencia": "N/D",
      "valor": 4500.0,
      "situacao": "Recebido"
    }
  ],
  "screenshot_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "timestamp": "2026-03-16T00:22:16+00:00"
}
```

> **Nota:** `data_nascimento` e `nis` podem ser `null` — o portal exibe esses campos apenas para algumas categorias de pessoas. `competencia` aparece como `"N/D"` porque a página de detalhes de cada benefício exige resolução de CAPTCHA; o valor total recebido, o nome do benefício e a localidade são extraídos da página pública sem restrição.

---

## Fluxo de execução

```
POST /api/v1/consulta
        │
        ▼
 ConsultaService.executar()
        │
        ├─► BrowserManager (async context manager)
        │         │
        │         └─► Playwright Chromium (headless, isolado por requisição)
        │
        └─► TransparenciaScraper
                  │
                  ├─1─► GET /pessoa-fisica/busca/lista?termo=...
                  ├─2─► fill("#termo") + (opcional) check("#beneficiarioProgramaSocial")
                  ├─3─► press Enter → aguarda networkidle
                  ├─4─► Se URL redireciona para /busca/pessoa-fisica/... → já no detalhe
                  │     Senão: verifica #countResultados; se 0 → erro "0 resultados"
                  ├─5─► Se NOME: clica em a.link-busca-nome (primeiro resultado)
                  ├─6─► JS extrai section.dados-tabelados → nome, CPF, localidade
                  ├─7─► Captura screenshot → Base64
                  └─8─► JS extrai #accordion-recebimentos-recursos → benefícios + valor
                              │
                              ▼
                     ConsultaResponse (JSON padronizado)
```

---

## Decisões técnicas

### Por que Playwright?
Playwright suporta `async/await` nativamente, permitindo execuções paralelas sem bloqueio. É mais robusto que Selenium para SPAs modernas e possui API mais expressiva para aguardar estados de rede.

### Por que FastAPI?
FastAPI é assíncrono por natureza (ASGI), se integrando perfeitamente com Playwright async. A geração automática de Swagger/OpenAPI e validação via Pydantic eliminam boilerplate.

### Por que sem estado global no scraper?
Cada requisição cria sua própria instância `BrowserManager` → `BrowserContext` → `Page`. Isso garante que consultas simultâneas não compartilhem estado de cookies, sessão ou DOM, eliminando condições de corrida.

### Por que screenshot sempre em Base64?
Evita dependência de storage externo (S3, disco) e simplifica o contrato da API. O cliente recebe tudo em um único JSON, podendo salvar o PNG localmente se precisar.

### Por que não acessar as páginas de detalhe dos benefícios?
As URLs `/beneficios/{programa}/{nis}` exigem resolução de CAPTCHA (AWS WAF). O scraper extrai os dados disponíveis na página pública da pessoa (nome do benefício e valor total recebido) sem acionar esse bloqueio.

---

## Seletores reais do portal (referência)

Mapeados via inspeção do HTML real em março/2026:

| Elemento | Seletor |
|---|---|
| Campo de busca | `#termo` |
| Checkbox filtro social | `#beneficiarioProgramaSocial` |
| Botão submeter | `Enter` no campo `#termo` (botão está fora do viewport) |
| Link de resultado | `a.link-busca-nome` |
| Contador de resultados | `#countResultados` |
| Dados da pessoa | `section.dados-tabelados` → `strong` + `span` adjacentes |
| Campo localidade | chave `"Localidade"` (não "Município") |
| Accordion benefícios | `#accordion-recebimentos-recursos` |
| Tabela de benefício | `strong[texto]` → `table` irmão seguinte |

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `HEADLESS` | `true` | Rodar browser em modo headless |
| `TIMEOUT_MS` | `30000` | Timeout máximo por consulta (ms) |
| `LOG_LEVEL` | `INFO` | Nível de log (DEBUG/INFO/WARNING/ERROR) |
| `PORT` | `8000` | Porta da API |
| `CORS_ORIGINS` | `*` | Origens CORS (separadas por vírgula) |
| `MAX_BROWSER_INSTANCES` | `5` | Instâncias simultâneas máximas |
| `RATE_LIMIT_PER_MINUTE` | `10` | Limite de requisições por minuto por IP |

---

## Privacidade

- CPF e NIS **nunca são logados** em produção
- Screenshots podem conter dados pessoais — trate com responsabilidade
- Use apenas para consultas autorizadas de dados públicos
