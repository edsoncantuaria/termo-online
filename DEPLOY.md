# Deploy — Termo Online

## Requisitos

- Python 3.11+
- Node.js 20+ (só para build do frontend)
- Ou Docker

## Build de produção

```bash
make install
make run
```

O servidor sobe em `http://0.0.0.0:8000` (variável `PORT`). O Vue compilado fica em `src/static/dist/`.

## Docker (recomendado)

```bash
docker compose up --build -d
```

Dados persistentes no volume `termo-data` (`data/termo.db`).

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PORT` | `8000` | Porta HTTP |
| `TERM0_DATA` | `./data` | Diretório do SQLite |
| `TERM0_LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `WARNING`, …) |
| `TERM0_REDIS_URL` | — | Redis para **rate limit** compartilhado entre workers; sem URL = memória |

## HTTPS e domínio

Coloque um reverse proxy (Caddy, nginx, Traefik) na frente do container ou do `make run`:

- Proxy para `http://127.0.0.1:8000`
- WebSocket em `/ws` com upgrade habilitado
- Cabeçalhos `X-Forwarded-*` se o proxy suportar

## Checklist pós-deploy

1. Abrir `/` — UI Vue carrega
2. `GET /api/health` e `GET /api/ready`
3. `GET /api/metricas` (opcional, por processo)
4. WebSocket da arena (`/ws/sala/...`)
5. Arquivos estáticos: `/sounds/`, `/assets/`, `favicon.svg`
6. PWA: `manifest.webmanifest` e service worker (opcional)

Backup local: `make backup-db`

## Atualização

```bash
git pull
make install
make run
# ou: docker compose up --build -d
```

O banco SQLite em `data/termo.db` é preservado se o volume/diretório `data/` for mantido.

## Escala horizontal (importante)

Salas da arena, fila ranqueada e matchmaking ficam **na memória do processo** Python. Para um único servidor (`make run` ou um container), está ok.

Se subir **mais de uma instância** atrás do load balancer:

- Jogadores na mesma sala precisam cair no **mesmo worker** (sticky session por cookie/IP), **ou**
- Migrar **salas e fila ranqueada** para Redis (ou sticky session no load balancer).

Com `TERM0_REDIS_URL`, o **rate limit** da API já é compartilhado entre instâncias. Salas/fila ainda ficam na memória de cada processo.

Sem sticky session ou Redis para salas, partidas na arena podem “sumir” entre requisições. WebSocket exige proxy com upgrade (`/ws`, `/ws/lobby`).

## Fuso horário

Diária, cap de XP e metas semanais usam **America/Sao_Paulo (UTC−3)** no servidor (`nucleo/tempo_brasil.py`).
