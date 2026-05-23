"""Versão do produto (semver simplificado para o jogador).

Política:
- Mudança significativa no jogo (regras, UX importante, modo, persistência): +0.1
  (1.0 → 1.1 → 1.2). O patch (terceiro número) pode subir para builds internos.
- Funcionalidade grande ou marco de produto: +1.0 no minor e zera o patch
  (ex.: 1.9 → 2.0).

Fonte única: ajuste aqui e espelhe em frontend/src/config/versao.js e
frontend/index.html (meta termo-version e <title>).
"""

VERSAO = "1.1.0"


def RotuloDeVersao(Numero: str) -> str:
    """Release minor/major: v1.1. Bugfix (patch > 0): v1.1.1."""
    Partes = Numero.strip().split(".")
    if len(Partes) >= 3:
        try:
            Patch = int(Partes[2])
        except ValueError:
            Patch = 0
        if Patch > 0:
            return f"v{Partes[0]}.{Partes[1]}.{Partes[2]}"
    if len(Partes) >= 2:
        return f"v{Partes[0]}.{Partes[1]}"
    return f"v{Numero}"


ROTULO = RotuloDeVersao(VERSAO)


def InfoVersao() -> dict:
    return {"versao": VERSAO, "rotulo": ROTULO}
