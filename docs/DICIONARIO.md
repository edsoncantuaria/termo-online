# Dicionário de palavras válidas

## Origem

O arquivo `src/dicionario.txt` lista substantivos/adjetivos/verbos de 5 letras em português, gerados via Hunspell (`make dicionario`).

## Normalização

- Comparação **sem acento** (`unidecode`), minúsculas.
- Exibição pode usar a forma com acento do par no dicionário.

## API

- `GET /api/dicionario/info` — `hash` (cache do cliente) e `total`.
- Chutes validados sempre no servidor; o cache no navegador só antecipa feedback.

## Critérios ao regenerar

1. Exatamente 5 letras após normalização.
2. Evitar abreviações e siglas obscuras quando possível.
3. Manter pares com/sem acento alinhados no índice do array.
