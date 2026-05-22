# Dicionário de palavras válidas

## Origem

O arquivo `src/dicionario.txt` lista palavras de 5 letras em português, extraídas de `dicionario/dicionario.db` (`make dicionario`).

O banco deve conter a tabela `words` com a coluna `word`. A pasta `dicionario/` não entra no repositório (`.gitignore`); copie ou gere o `dicionario.db` localmente antes de regenerar.

## Normalização

- Comparação **sem acento** (`unidecode`), minúsculas.
- Exibição pode usar a forma com acento do par no dicionário.
- Várias grafias com acento para a mesma chave sem acento: fica a forma acentuada preferida (ordem alfabética entre elas).

## API

- `GET /api/dicionario/info` — `hash` (cache do cliente) e `total`.
- `GET /api/dicionario/palavras` — lista normalizada (sem acento) para cache offline no navegador.
- Chutes validados sempre no servidor; o cache no navegador só antecipa feedback.

## Critérios ao regenerar

1. Exatamente 5 letras (comprimento da string no banco).
2. Apenas letras do alfabeto português (inclui acentos).
3. Pelo menos 2 vogais; sem sequência de 4+ consoantes.
4. Uma entrada por palavra normalizada (sem acento).

## Script legado

`scripts/gerar_dicionario.py` ainda gera a partir do Hunspell, caso precise comparar ou migrar listas antigas.
