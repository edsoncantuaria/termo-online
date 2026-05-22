"""Avatares ilustrados — IDs fixos, mesma família visual."""

AVATAR_PADRAO = "folha"

AVATARES: tuple[str, ...] = (
    "folha",
    "broto",
    "sol",
    "nuvem",
    "cogumelo",
    "coruja",
    "raposa",
    "gato",
    "peixe",
    "abelha",
    "tulipa",
    "pinheiro",
)

_AVATARES_SET = frozenset(AVATARES)


def AvatarValido(AvatarId: str | None) -> bool:
    return bool(AvatarId) and AvatarId in _AVATARES_SET


def AvatarPadraoDeNick(Nick: str) -> str:
    """Avatar estável derivado do nick (antes de escolha explícita)."""
    s = (Nick or "?").strip().lower()
    h = 0
    for c in s:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return AVATARES[h % len(AVATARES)]


def ResolverAvatarId(AvatarSalvo: str | None, Nick: str) -> str:
    if AvatarValido(AvatarSalvo):
        return AvatarSalvo  # type: ignore[return-value]
    return AvatarPadraoDeNick(Nick)
