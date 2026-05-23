#!/bin/sh
# Instalação de produção na VM (Alpine/Linux).
#
# Uso (na VM, como root):
#   git clone <repo> /root/termo-online
#   cd /root/termo-online
#   sh deploy/vm/instalar-na-vm.sh
#
# Ou, na raiz do clone:
#   sudo sh instalar.sh
#
# Requer: cloudflared apontando termo.cloudive.com.br -> :8000 e api-termo -> :8001
set -eu

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$RAIZ"

API_ORIGIN="${VITE_API_ORIGIN:-https://api-termo.cloudive.com.br}"
MARCA_CLOUDIVE="${VITE_MARCA_CLOUDIVE:-true}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Erro: rode como root (ex.: su - && cd $RAIZ && sh deploy/vm/instalar-na-vm.sh)"
  exit 1
fi

echo "==> Termo Online — instalação em $RAIZ"
echo "    API: $API_ORIGIN"
echo "    Frontend: porta 8000 | API: porta 8001"

echo "==> Pacotes do sistema (Python + Node)"
if command -v apk >/dev/null 2>&1; then
  apk add --no-cache python3 py3-pip nodejs npm curl 2>/dev/null || true
elif command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq python3 python3-venv python3-pip nodejs npm curl
fi

echo "==> Ambiente Python"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

echo "==> Banco SQLite"
mkdir -p data
TERM0_DATA="$RAIZ/data" .venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
from nucleo import persistencia
persistencia.InicializarBanco()
print('Banco OK:', persistencia.CaminhoBanco)
"

echo "==> Build do frontend"
cd frontend
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi
VITE_API_ORIGIN="$API_ORIGIN" VITE_MARCA_CLOUDIVE="$MARCA_CLOUDIVE" npm run build
cd "$RAIZ"

if [ ! -f src/static/dist/index.html ]; then
  echo "Erro: build Vue falhou (src/static/dist/index.html ausente)"
  exit 1
fi

INST="$RAIZ"
SERVICO_API=termo-api
SERVICO_WEB=termo-web

if [ -d /etc/systemd/system ] && command -v systemctl >/dev/null 2>&1; then
  echo "==> Serviços systemd"
  sed -e "s|/root/termo-online|$INST|g" deploy/vm/termo-api.service > /etc/systemd/system/termo-api.service
  sed -e "s|/root/termo-online|$INST|g" deploy/vm/termo-web.service > /etc/systemd/system/termo-web.service
  systemctl daemon-reload
  systemctl enable "$SERVICO_API" "$SERVICO_WEB"
  systemctl restart "$SERVICO_API" "$SERVICO_WEB"
elif command -v rc-service >/dev/null 2>&1; then
  echo "==> Serviços OpenRC (Alpine)"
  for svc in termo-api termo-web; do
    sed "s|__INSTALL_DIR__|$INST|g" "deploy/vm/openrc/$svc" > "/etc/init.d/$svc"
    chmod +x "/etc/init.d/$svc"
  done
  rc-update add "$SERVICO_API" default 2>/dev/null || true
  rc-update add "$SERVICO_WEB" default 2>/dev/null || true
  rc-service "$SERVICO_API" stop 2>/dev/null || true
  rc-service "$SERVICO_WEB" stop 2>/dev/null || true
  rc-service "$SERVICO_API" start
  rc-service "$SERVICO_WEB" start
else
  echo "==> Sem systemd/OpenRC — iniciando em background"
  pkill -f "uvicorn main:Aplicacao.*8001" 2>/dev/null || true
  pkill -f "servir_frontend.py" 2>/dev/null || true
  (
    cd "$INST/src" && export PORT=8001 TERM0_API_ONLY=1 TERM0_RELOAD=0 \
      TERM0_DATA="$INST/data" \
      TERM0_CORS_ORIGINS="https://termo.cloudive.com.br,http://localhost:8000" \
      TERM0_LOG_LEVEL=INFO
    nohup "$INST/.venv/bin/python" -m uvicorn main:Aplicacao \
      --host 0.0.0.0 --port 8001 --app-dir "$INST/src" \
      >>"$INST/data/termo-api.log" 2>&1 &
  )
  (
    cd "$INST" && export PORT=8000
    nohup "$INST/.venv/bin/python" "$INST/src/servir_frontend.py" \
      >>"$INST/data/termo-web.log" 2>&1 &
  )
  echo "    Logs: $INST/data/termo-api.log e termo-web.log"
  echo "    Configure OpenRC ou systemd para persistir após reboot."
fi

echo ""
echo "==> Verificação"
if command -v systemctl >/dev/null 2>&1 && [ -d /etc/systemd/system ]; then
  systemctl is-active "$SERVICO_API" "$SERVICO_WEB" 2>/dev/null || true
elif command -v rc-service >/dev/null 2>&1; then
  rc-service "$SERVICO_API" status 2>/dev/null || true
  rc-service "$SERVICO_WEB" status 2>/dev/null || true
fi
ApiOk=0
I=0
while [ "$I" -lt 15 ]; do
  if curl -sf http://127.0.0.1:8001/api/health >/dev/null; then
    ApiOk=1
    break
  fi
  I=$((I + 1))
  sleep 1
done
if [ "$ApiOk" -eq 1 ]; then
  curl -sf http://127.0.0.1:8001/api/health | head -c 200
  echo ""
  echo "API /api/health OK"
else
  echo "API falhou — veja: rc-service termo-api status e tail data/termo-api.log"
fi
curl -sf -o /dev/null -w "Frontend HTTP %{http_code}\n" http://127.0.0.1:8000/ || echo "Frontend falhou"
if [ -f src/static/dist/index.html ]; then
  echo "Build frontend: $(stat -c %y src/static/dist/index.html 2>/dev/null || stat -f %Sm src/static/dist/index.html)"
fi

echo ""
echo "Pronto. Confirme no Cloudflare Tunnel:"
echo "  termo.cloudive.com.br      -> http://127.0.0.1:8000"
echo "  api-termo.cloudive.com.br  -> http://127.0.0.1:8001"
echo ""
echo "Atualizar depois: cd $RAIZ && git pull && sh deploy/vm/instalar-na-vm.sh"
