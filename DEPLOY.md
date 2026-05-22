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

## Escala horizontal (importante)

Salas da arena, fila ranqueada e matchmaking ficam **na memória do processo** Python. Para um único servidor (`make run` ou um container), está ok.

Se subir **mais de uma instância** atrás do load balancer:

- Jogadores na mesma sala precisam cair no **mesmo worker** (sticky session por cookie/IP), **ou**
- Migrar estado para **Redis** (filas, salas, WebSocket pub/sub).

Sem isso, sala/fila podem “sumir” entre requisições. WebSocket exige proxy com upgrade (`/ws`, `/ws/lobby`).

## Fuso horário

Diária, cap de XP e metas semanais usam **America/Sao_Paulo (UTC−3)** no servidor (`nucleo/tempo_brasil.py`).
