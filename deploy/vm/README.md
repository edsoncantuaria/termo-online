# Deploy na VM (termo.cloudive.com.br)

## Pré-requisitos na VM

- **root** (para systemd nas portas 8000 e 8001)
- **cloudflared** já configurado:
  - `termo.cloudive.com.br` → `http://127.0.0.1:8000` (frontend)
  - `api-termo.cloudive.com.br` → `http://127.0.0.1:8001` (API + WebSocket)

## Instalação em um comando (após clone)

```bash
bd-iamlive          # ou ssh na VM
su -                # senha de root
git clone <url-do-repo> /root/termo-online
cd /root/termo-online
sh instalar.sh
```

O script `instalar.sh` (ou `deploy/vm/instalar-na-vm.sh`) faz tudo:

1. Instala Python 3 + Node (apk/apt)
2. Cria `.venv` e instala `requirements.txt`
3. Inicializa `data/termo.db`
4. Build do Vue com `VITE_API_ORIGIN=https://api-termo.cloudive.com.br`
5. Sobe **termo-web** (porta 8000) e **termo-api** (porta 8001) via systemd

## Atualizar versão

```bash
cd /root/termo-online
git pull
sh instalar.sh
```

## Variáveis opcionais

```bash
VITE_API_ORIGIN=https://api-termo.cloudive.com.br \
VITE_MARCA_CLOUDIVE=true \
sh instalar.sh
```

## Sincronizar da máquina local (sem git na VM)

Na sua máquina, com `rsync` instalado:

```bash
sh deploy/vm/sincronizar.sh
# na VM como root:
mv /home/alpine/termo-online-upload /root/termo-online
cd /root/termo-online && sh instalar.sh
```

## Arquivos

| Arquivo | Função |
|---------|--------|
| `instalar-na-vm.sh` | Instalação completa |
| `termo-api.service` | API FastAPI :8001 |
| `termo-web.service` | Estáticos Vue :8000 |
| `sincronizar.sh` | Envia código via rsync (opcional) |
