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

## HTTPS e domínio

Coloque um reverse proxy (Caddy, nginx, Traefik) na frente do container ou do `make run`:

- Proxy para `http://127.0.0.1:8000`
- WebSocket em `/ws` com upgrade habilitado
- Cabeçalhos `X-Forwarded-*` se o proxy suportar

## Checklist pós-deploy

1. Abrir `/` — UI Vue carrega
2. `GET /api/health` ou criar partida de prática
3. WebSocket da arena (`/ws/sala/...`)
4. Arquivos estáticos: `/sounds/`, `/assets/`, `favicon.svg`
5. PWA: `manifest.webmanifest` e service worker (opcional)

## Atualização

```bash
git pull
make install
make run
# ou: docker compose up --build -d
```

O banco SQLite em `data/termo.db` é preservado se o volume/diretório `data/` for mantido.
