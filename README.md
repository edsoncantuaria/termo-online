# Termo Online · v1.0

Jogo de palavras em português — moderno e social. Conta opcional (visitante sem cadastro). Primeira versão de produção.

## Modos

| Modo | Descrição |
|------|-----------|
| **Palavra do dia** | Mesma palavra para todos, **uma vez por dia** (validado no servidor) |
| **Prática** | Palavras aleatórias — normal ou **difícil** |
| **Dueto** | 2 palavras, 7 tentativas (um chute vale para as duas) |
| **Quarteto** | 4 palavras, 9 tentativas |
| **Desafio** | Mesma palavra por código (`/?desafio=CODIGO`) |
| **Arena** | Salas 2–8 jogadores, maratona ou primeiro a N vitórias, chat, espectadores, revanche |
| **Ranqueado** | Em **Jogar** → aba Ranqueado: 1v1, matchmaking, elo e RP (conta registrada) |

## Funcionalidades

- **Home:** salas públicas ao vivo via **WebSocket** (`/ws/lobby`), com fallback HTTP e filtros
- **Arena:** QR e link da sala no lobby, confirmação ao sair
- **Jogo:** sons (teclas, chute, vitória, chat, entrada na sala), shake na linha inválida, dica visual na linha atual
- **UX:** tutorial na primeira visita, tema claro, PWA instalável, Open Graph
- **Conta:** registro/login ou visitante; ranking ranqueado e fila só com conta real
- **Perfil:** ranking ranqueado (elo), estatísticas, metas semanais e diárias
- Persistência em **SQLite** (`data/termo.db`)
- Retomar partida/sala via `localStorage` + servidor
- Link direto: `http://localhost:8000/?sala=CODIGO` ou `/?desafio=CODIGO`
- Compartilhar resultado (diária, prática e arena)
- Rate limit nas APIs (global e rotas sensíveis)
- `GET /api/health`, `/api/ready`, `/api/metricas`
- Arena em tempo real: **WebSocket** por sala (`/ws/sala/...`) + sync HTTP no lobby

Ver [DEPLOY.md](DEPLOY.md) para colocar em produção.

### Modos da Arena

| Modo | Como vence |
|------|------------|
| **Pontos infinitos** | Maratona: cada rodada soma pontos; quem tiver mais pontos quando o host encerrar vence |
| **Primeiro a N vitórias** | Quem vencer mais rodadas primeiro (ex.: 5 vitórias) leva a sessão |

### Conta e ranqueada

| Tipo | O que libera |
|------|----------------|
| **Visitante** | Nick amigável automático (`maria`, `maria1`, `joao2`…); sem fila ranqueada nem ranking de elo; após **1 h** sem uso o nick volta a ficar livre para outro visitante |
| **Conta** | Nick fixo; ao cadastrar, se o nick estiver só com visitante, a conta fica com o nick e o visitante é renomeado (ex.: `maria1` → `maria10`) |

O modal de conta abre em **Entrar**; **Entrar como visitante** fica acima do login.

**Elos (pontos RP):** Papelão (0–399) → Madeira → Ferro → Bronze → **Prata** → Ouro → Platina → Diamante → Estrela (3200+). Início em **0 RP**; até a 1ª partida ranqueada o rótulo é **Sem Rank**. Cada elo tem cor própria nas salas online.

**Nível e XP (conta registrada):** níveis infinitos com anel colorido no avatar (faixa muda a cada 10 níveis). XP só com login validado no servidor.

| Ação | XP base |
|------|---------|
| Tentativa na palavra do dia | +10 |
| Acertar na diária (na mesma tentativa) | +35 extra |
| Concluir a diária do dia | +20 |
| Chute na prática | +4 |
| Vencer na prática | +15 extra |
| Duelo ranqueado | +45 (+20 se vencer) |
| Rodada na arena | +14 (+8 se vencer a rodada) |
| Campeão da sessão (arena) | +25 |

**Curva de progressão:** sobe **rápido no início** (nível 1→2 custa ~50 XP; ganho 100% do base) e **fica mais difícil** depois (custo por nível sobe com marcos a cada 10/25; ganho efetivo cai até ~15% do base em níveis altos). **Teto diário alto:** até **2200 XP/dia** por conta (anti-farm; o restante volta no dia seguinte).

**Metas semanais:** 3 diárias na semana, 3 duelos ranqueados, 5 rodadas na arena — XP bônus automático ao concluir.

**Diária séria:** uma partida por **conta + data** (dia em horário de Brasília); tentativas e XP não repetem ao recarregar. Exige conta (não visitante).

**Revanche ranqueada:** após duelo PvP real, `POST /api/ranqueada/revanche` prioriza o mesmo oponente se os dois pedirem.

**Duelo ranqueado:** vitória **+16 a +20** RP, derrota **-8 a -12**, conforme diferença de rating do oponente. Cálculo e persistência **somente no servidor** (`POST /api/pontuacao/registrar` retorna 403).

**Matchmaking (1v1):** busca **competitiva** por faixa de RP que **abre com o tempo**:

| Tempo na fila | Janela ±RP (aprox.) | Comportamento |
|---------------|----------------------|---------------|
| 0s | ~75 (+ ajuste da faixa de elo) | Só oponentes muito próximos |
| +1s | +12 RP por segundo | Quem espera mais aceita adversários um pouco mais distantes |
| 4s | ~123 | Fim da “busca estrita”; pode reservar oponente na fila |
| 14s | até ~320 | Se não houver humano compatível, entra duelo com oponente reservado (bot) |

**Bots na fila (temporário):** ~100 oponentes artificiais só em **Madeira, Papelão, Ferro e Bronze** (nenhum em Ouro para cima), com mais densidade nos elos baixos. No futuro, use `TERM0_BOTS_RANQUEADOS=0` para só PvP real.

- Pareamento **real × real:** escolhe o par com RP **mais próximo** entre quem está na janela (não é “o primeiro da fila”).
- **Mesmo elo** (ex.: Ferro com Ferro): +45 RP de tolerância.
- Regras em `src/nucleo/matchmaking_competitivo.py`; status da fila devolve `busca.janelaRp`, `rpMinimo`, `rpMaximo`.

APIs: `POST /api/auth/registrar` (nick, e-mail, senha), `/login` (e-mail ou nick), `/visitante`, `GET /api/auth/eu`, `POST/GET/DELETE /api/ranqueada/fila`, `GET /api/ranqueada/ranking`.

### Pontuação (modo pontos)

| Tentativa em que acertou | Pontos |
|--------------------------|--------|
| 1ª | 6 |
| 2ª | 5 |
| 3ª | 4 |
| 4ª | 3 |
| 5ª | 2 |
| 6ª | 1 |
| Não acertou | 0 |

## Como rodar

**Primeira vez:**

```bash
make install
```

**Desenvolvimento:**

```bash
make dev
```

Abra **http://localhost:5173** (UI com hot-reload). API em **http://localhost:8000**.

**Produção local:**

```bash
make run
```

| Comando | O que faz |
|---------|-----------|
| `make install` | Python + `npm install` no `frontend/` |
| `make install-dev` | install + pytest + gerador de dicionário |
| `make dev` | API `:8000` + Vite `:5173` |
| `make run` | Build Vue → `src/static/dist/` + só `:8000` |
| `make test` | pytest (backend) |
| `make backup-db` | backup SQLite em `data/backups/` |

### Frontend (Vue)

```
frontend/src/
  stores/termo.js      — estado Pinia
  stores/termo/acoes-ranqueada.js, acoes-arena.js
  services/api.js
  components/          — views, jogo, arena, dialogs, ui
  lib/som.js           — efeitos sonoros (Kenney CC0)
```

Testes E2E (opcional, com API rodando ou `reuseExistingServer`):

```bash
cd frontend && npm run test:e2e
```

### Docker

```bash
docker compose up --build
```

### Testes backend

```bash
make test
```

### Dicionário

Requer `dicionario/dicionario.db` localmente (ver `docs/DICIONARIO.md`).

```bash
make install-dev
make dicionario
```

## Stack

Python · FastAPI · WebSocket · SQLite · **Vue 3** · Vite · Pinia · PWA

## Convenções

Código em português com CamelCase — ver `.cursor/rules/termo-portugues.mdc`.
