#!/bin/sh
# Na sua máquina local (raiz do projeto termo-online):
#   sh deploy/vm/sincronizar.sh
set -eu

HOST="${DEPLOY_HOST:-alpine@137.131.168.10}"
KEY="${DEPLOY_KEY:-$HOME/Documentos/ssh-bd/ssh-key-2026-04-03.key}"
DEST="${DEPLOY_DEST:-/home/alpine/termo-online-upload}"

RSYNC_SSH="ssh -i $KEY -o StrictHostKeyChecking=accept-new"

rsync -avz --delete -e "$RSYNC_SSH" \
  --exclude .venv \
  --exclude node_modules \
  --exclude frontend/node_modules \
  --exclude data/termo.db \
  --exclude .git \
  ./ "$HOST:$DEST/"

echo ""
echo "Arquivos em $HOST:$DEST"
echo "Conecte: bd-iamlive"
echo "Depois:  su -"
echo "         mv /home/alpine/termo-online-upload /root/termo-online   # ou rsync para /root se tiver acesso"
echo "         cd /root/termo-online && sh deploy/vm/instalar-na-vm.sh"
