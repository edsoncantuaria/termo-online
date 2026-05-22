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

echo "==> Serviços systemd"
INST="$RAIZ"
sed \
  -e "s|/root/termo-online|$INST|g" \
  deploy/vm/termo-api.service > /etc/systemd/system/termo-api.service
sed \
  -e "s|/root/termo-online|$INST|g" \
  deploy/vm/termo-web.service > /etc/systemd/system/termo-web.service

systemctl daemon-reload
systemctl enable termo-api termo-web
systemctl restart termo-api termo-web

sleep 2
echo ""
echo "==> Verificação"
systemctl is-active termo-api termo-web || true
curl -sf http://127.0.0.1:8001/api/health && echo "API /api/health OK" || echo "API falhou"
curl -sf -o /dev/null -w "Frontend HTTP %{http_code}\n" http://127.0.0.1:8000/ || echo "Frontend falhou"

echo ""
echo "Pronto. Confirme no Cloudflare Tunnel:"
echo "  termo.cloudive.com.br      -> http://127.0.0.1:8000"
echo "  api-termo.cloudive.com.br  -> http://127.0.0.1:8001"
echo ""
echo "Atualizar depois: cd $RAIZ && git pull && sh deploy/vm/instalar-na-vm.sh"
