# Deploy Alpine — simples e leve

Sem Docker, sem nginx, sem Caddy na VM. O túnel Cloudflare fala direto com dois processos Python.

## Stack (recomendado)

```
Internet → cloudflared → 127.0.0.1:8000  (termo-web, UI estática)
                      → 127.0.0.1:8001  (termo-api, API + WebSocket)
                      → data/termo.db   (SQLite)
```

| Peça | RAM típica | Obrigatório? |
|------|------------|--------------|
| `termo-web` | ~30–50 MB | Sim |
| `termo-api` (**1 processo** uvicorn) | ~80–150 MB | Sim |
| SQLite | disco | Sim |
| Redis | ~15–32 MB | Sim — `instalar.sh` instala e configura |
| nginx / Caddy / Traefik | — | **Não** |

**Por que não colocar proxy na VM?** HTTPS e domínio já vêm do Cloudflare. Proxy extra só duplica processo, RAM e ponto de falha — sem ganho no modelo de **uma API**.

## Instalação

```bash
su -
git clone <repo> /root/termo-online
cd /root/termo-online
sh deploy/vm/instalar-na-vm.sh
```

Túnel (já na sua VM):

- `termo.cloudive.com.br` → `http://127.0.0.1:8000`
- `api-termo.cloudive.com.br` → `http://127.0.0.1:8001`

WebSocket (`/ws/lobby`, `/ws/sala/...`) funciona no mesmo origin da API — o tunnel encaminha upgrade sem config extra.

## Controle de carga (simples e poderoso)

O próprio Termo limita sobrecarga **dentro do processo** — não precisa fila externa.

**Perfil padrão:** VM com **1 GB RAM + 3 GB swap** (sua Cloudive). Os tetos permitem escalar até o swap; em pico o kernel usa swap, não derruba o serviço de uma vez.

| Variável | Padrão (1G+3G swap) | O que faz |
|----------|---------------------|-----------|
| `TERM0_MAX_WS_SALA` | 700 | Conexões WebSocket na arena |
| `TERM0_MAX_WS_LOBBY` | 400 | Conexões no lobby |
| `TERM0_MAX_SALAS` | 280 | Salas vivas em memória |
| `TERM0_MAX_FILA_RANQUEADA` | 150 | Humanos na fila 1v1 |
| `TERM0_BOTS_RANQUEADOS` | `1` | `0` desliga bots na fila (só PvP real quando a base crescer) |
| `TERM0_MAX_FILA_ESPERA` | 200 | Fila quando WS sala cheio |

Cheio → HTTP **503** + `Retry-After`, ou WebSocket **1013**.

```bash
curl -s http://127.0.0.1:8001/api/infra/carga
curl -s http://127.0.0.1:8001/api/metricas
free -h    # RAM + swap em uso
```

**VM menor (512 MB, sem swap):** reduza no `/etc/init.d/termo-api`, por exemplo `TERM0_MAX_WS_SALA=300` e `TERM0_MAX_SALAS=120`.

**Mais folga (2 GB RAM):** pode subir `TERM0_MAX_WS_SALA=1000` e `TERM0_MAX_SALAS=400`.

## Visitante

Visitante joga na arena e modos casuais, mas **não** entra em ranking nem fila ranqueada — só conta com e-mail.

## Atualizar (UI + API)

**`git pull` sozinho não muda a interface.** O Vue compilado fica em `src/static/dist/`, que **não vai no Git** (`.gitignore`).

```bash
cd /root/termo-online
sh atualizar.sh
```

Isso faz: `git pull` → `npm run build` → reinicia `termo-api` e `termo-web`.

Primeira instalação ou Node/Python novos: use `sh instalar.sh` (inclui Redis local + `TERM0_REDIS_URL` no `termo-api`).

```bash
redis-cli ping          # PONG
rc-service redis status # Alpine
```

No celular/PC, depois do deploy: **recarregar forçado** (Ctrl+Shift+R) ou fechar e abrir o app — o PWA pode guardar cache antigo por alguns segundos (`autoUpdate`).

## Checklist

1. `curl -s http://127.0.0.1:8001/api/health`
2. `curl -s http://127.0.0.1:8001/api/ready`
3. Criar sala + WebSocket na arena
4. Ranqueado com conta real (visitante → 403)
5. Mobile: tela cheia + teclado

---

## Só se um dia precisar de 2+ APIs (raro)

Na Cloudive com **um** `termo-api`, ignore esta seção.

| Necessidade | Solução leve |
|-------------|--------------|
| Fila ranqueada entre processos | Redis local (`deploy/vm/redis-alpine.conf`, ~32 MB) + `TERM0_REDIS_URL` |
| Salas / WebSocket no mesmo nó | **Um origin** no tunnel (`:8001` só) — não balancear entre portas |
| Rate limit compartilhado | Mesmo Redis |

**Não suba nginx na VM** só por sticky: prefira **não escalar horizontalmente** até precisar de segundo servidor. Se precisar, use session affinity no **Cloudflare Load Balancing** ou um segundo origin dedicado — não um proxy genérico na mesma máquina.

Diagnóstico se algo cair no worker errado: cabeçalho `X-Termo-Worker` em respostas 503.
