#!/bin/sh
# Atalho na raiz do repositório → instalação na VM.
exec sh "$(dirname "$0")/deploy/vm/instalar-na-vm.sh" "$@"
