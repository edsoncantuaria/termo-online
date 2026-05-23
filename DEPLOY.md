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

Inclui **Redis** (`redis:7-alpine`) com `TERM0_REDIS_URL=redis://redis:6379/0` no serviço `termo` (fila ranqueada e rate limit entre processos). Para subir só a API sem Redis, remova o serviço `redis` e a variável no `docker-compose.yml`.

Dados persistentes no volume `termo-data` (`data/termo.db`).

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PORT` | `8000` | Porta HTTP |
| `TERM0_DATA` | `./data` | Diretório do SQLite |
| `TERM0_LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `WARNING`, …) |
| `TERM0_REDIS_URL` | — | Redis (fila ranqueada + rate limit); no Compose já aponta para `redis://redis:6379/0` |

## HTTPS e domínio

**VM Alpine (produção Cloudive):** use **Cloudflare Tunnel** direto em `:8000` (UI) e `:8001` (API) — sem nginx/Caddy na máquina. Ver [deploy/vm/DEPLOY-ALPINE.md](deploy/vm/DEPLOY-ALPINE.md).

**Outros ambientes:** proxy opcional (Caddy, nginx) só se não tiver tunnel/terminação externa — proxy para `http://127.0.0.1:8000`, WebSocket em `/ws` com upgrade, cabeçalhos `X-Forwarded-*`.

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

## Escala e carga

**Limites por processo** (anti-sobrecarga): `TERM0_MAX_WS_SALA`, `TERM0_MAX_WS_LOBBY`, `TERM0_MAX_SALAS`, `TERM0_MAX_FILA_RANQUEADA`. Ver `GET /api/infra/carga` e `GET /api/metricas`.

**Instância única** (`make run`, um OpenRC `termo-api`): recomendado em VM pequena — salas, WebSocket e fila na mesma RAM.

**Escala (só se tiver 2+ processos API):** fila ranqueada via Redis (`TERM0_REDIS_URL`); salas/WebSocket ficam no processo que criou a sala — na prática use **uma instância** ou **um origin** no tunnel (sem nginx na VM). Detalhes em [deploy/vm/DEPLOY-ALPINE.md](deploy/vm/DEPLOY-ALPINE.md).

**Alpine sem Docker:** [deploy/vm/DEPLOY-ALPINE.md](deploy/vm/DEPLOY-ALPINE.md).

## Fuso horário

Diária, cap de XP e metas semanais usam **America/Sao_Paulo (UTC−3)** no servidor (`nucleo/tempo_brasil.py`).
