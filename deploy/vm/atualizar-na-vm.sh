#!/bin/sh
# Atualiza código + rebuild do Vue + reinicia serviços.
# git pull sozinho NÃO atualiza a interface (dist/ não está no repositório).
#
# Uso (na VM, como root):
#   cd /root/termo-online
#   sh deploy/vm/atualizar-na-vm.sh
# ou: sh atualizar.sh
set -eu

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$RAIZ"

API_ORIGIN="${VITE_API_ORIGIN:-https://api-termo.cloudive.com.br}"
MARCA_CLOUDIVE="${VITE_MARCA_CLOUDIVE:-true}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Erro: rode como root (su -)"
  exit 1
fi

echo "==> Termo Online — atualizar em $RAIZ"

if [ -d .git ]; then
  echo "==> git pull"
  git pull
else
  echo "==> Sem .git — usando arquivos já presentes"
fi

if [ ! -x .venv/bin/python ]; then
  echo "Erro: .venv ausente. Rode primeiro: sh instalar.sh"
  exit 1
fi

echo "==> Dependências Python (se mudou requirements.txt)"
.venv/bin/pip install -q -r requirements.txt

echo "==> Build do frontend (obrigatório para ver mudanças na UI)"
cd frontend
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi
VITE_API_ORIGIN="$API_ORIGIN" VITE_MARCA_CLOUDIVE="$MARCA_CLOUDIVE" npm run build
cd "$RAIZ"

if [ ! -f src/static/dist/index.html ]; then
  echo "Erro: build Vue falhou"
  exit 1
fi

echo "==> Reiniciar serviços"
if command -v rc-service >/dev/null 2>&1; then
  rc-service termo-api restart
  rc-service termo-web restart
elif command -v systemctl >/dev/null 2>&1; then
  systemctl restart termo-api termo-web
else
  echo "Reinicie termo-api e termo-web manualmente."
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
if [ "$ApiOk" -eq 1 ]; then echo "API OK"; else echo "API falhou (aguarde ou veja logs)"; fi
curl -sf -o /dev/null http://127.0.0.1:8000/ && echo "Frontend OK" || echo "Frontend falhou"

echo ""
echo "Pronto. No navegador: Ctrl+Shift+R (ou limpar cache do PWA)."
echo "Assets novos ficam em src/static/dist/assets/ com hash no nome."
