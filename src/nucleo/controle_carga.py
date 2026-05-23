"""Limites de carga por processo — evita sobrecarga de memória e conexões.

Padrões calibrados para VM ~1 GB RAM + swap (ex.: Alpine Cloudive).
Ajuste via TERM0_MAX_* se a máquina for menor ou maior.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass

_Bloqueio = threading.Lock()
_ConexoesWsSala = 0
_ConexoesWsLobby = 0
_FilaEsperaServidor: list[float] = []


def _IntEnv(Nome: str, Padrao: int) -> int:
    try:
        return max(0, int(os.environ.get(Nome, str(Padrao))))
    except ValueError:
        return Padrao


MAX_CONEXOES_WS_SALA = _IntEnv("TERM0_MAX_WS_SALA", 700)
MAX_CONEXOES_WS_LOBBY = _IntEnv("TERM0_MAX_WS_LOBBY", 400)
MAX_SALAS_ATIVAS = _IntEnv("TERM0_MAX_SALAS", 280)
MAX_FILA_RANQUEADA = _IntEnv("TERM0_MAX_FILA_RANQUEADA", 150)
MAX_FILA_ESPERA_SERVIDOR = _IntEnv("TERM0_MAX_FILA_ESPERA", 200)
TEMPO_ESPERA_SLOT_SEG = _IntEnv("TERM0_ESPERA_SLOT_SEG", 3)


@dataclass
class ResultadoAdmissao:
    Permitido: bool
    Mensagem: str | None = None
    PosicaoFila: int = 0
    RetryAfterSegundos: int = 0


def ContarConexoesWsSala() -> int:
    with _Bloqueio:
        return _ConexoesWsSala


def ContarConexoesWsLobby() -> int:
    with _Bloqueio:
        return _ConexoesWsLobby


def RegistrarConexaoWsSala() -> None:
    global _ConexoesWsSala
    with _Bloqueio:
        _ConexoesWsSala += 1


def LiberarConexaoWsSala() -> None:
    global _ConexoesWsSala
    with _Bloqueio:
        _ConexoesWsSala = max(0, _ConexoesWsSala - 1)
        _LiberarSlotsEspera()


def RegistrarConexaoWsLobby() -> None:
    global _ConexoesWsLobby
    with _Bloqueio:
        _ConexoesWsLobby += 1


def LiberarConexaoWsLobby() -> None:
    global _ConexoesWsLobby
    with _Bloqueio:
        _ConexoesWsLobby = max(0, _ConexoesWsLobby - 1)


def _LiberarSlotsEspera() -> None:
    global _FilaEsperaServidor
    Agora = time.time()
    _FilaEsperaServidor = [T for T in _FilaEsperaServidor if Agora - T < 300]
    while _FilaEsperaServidor and _TemCapacidadeWsInterno():
        _FilaEsperaServidor.pop(0)


def _TemCapacidadeWsInterno() -> bool:
    return _ConexoesWsSala < MAX_CONEXOES_WS_SALA


def PodeAceitarWsSala() -> ResultadoAdmissao:
    with _Bloqueio:
        if _TemCapacidadeWsInterno():
            return ResultadoAdmissao(True)
        if len(_FilaEsperaServidor) >= MAX_FILA_ESPERA_SERVIDOR:
            return ResultadoAdmissao(
                False,
                "Servidor cheio. Tente de novo em alguns minutos.",
                PosicaoFila=MAX_FILA_ESPERA_SERVIDOR,
                RetryAfterSegundos=30,
            )
        _FilaEsperaServidor.append(time.time())
        Pos = len(_FilaEsperaServidor)
        return ResultadoAdmissao(
            False,
            f"Aguarde na fila de conexão ({Pos}º)…",
            PosicaoFila=Pos,
            RetryAfterSegundos=TEMPO_ESPERA_SLOT_SEG,
        )


def PodeAceitarWsLobby() -> ResultadoAdmissao:
    with _Bloqueio:
        if _ConexoesWsLobby < MAX_CONEXOES_WS_LOBBY:
            return ResultadoAdmissao(True)
        return ResultadoAdmissao(
            False,
            "Lobby cheio. Atualize a página em instantes.",
            RetryAfterSegundos=8,
        )


def PodeCriarSala(SalasAtivas: int) -> ResultadoAdmissao:
    if SalasAtivas < MAX_SALAS_ATIVAS:
        return ResultadoAdmissao(True)
    return ResultadoAdmissao(
        False,
        "Muitas salas ativas no momento. Tente novamente em breve.",
        RetryAfterSegundos=15,
    )


def PodeEntrarFilaRanqueada(TamanhoFila: int, JaNaFila: bool) -> ResultadoAdmissao:
    if JaNaFila or TamanhoFila < MAX_FILA_RANQUEADA:
        return ResultadoAdmissao(True)
    return ResultadoAdmissao(
        False,
        "Fila ranqueada cheia. Aguarde alguns segundos e tente de novo.",
        PosicaoFila=TamanhoFila + 1,
        RetryAfterSegundos=10,
    )


def MontarStatusCarga(*, SalasAtivas: int, FilaRanqueada: int) -> dict:
    from .redis_estado import RedisHabilitado

    with _Bloqueio:
        Espera = len(_FilaEsperaServidor)
    Aviso = None
    if not RedisHabilitado():
        Aviso = (
            "Sem Redis: não rode vários workers com salas ativas — "
            "cada processo tem estado próprio."
        )
    return {
        "limites": {
            "maxWsSala": MAX_CONEXOES_WS_SALA,
            "maxWsLobby": MAX_CONEXOES_WS_LOBBY,
            "maxSalas": MAX_SALAS_ATIVAS,
            "maxFilaRanqueada": MAX_FILA_RANQUEADA,
        },
        "uso": {
            "wsSala": ContarConexoesWsSala(),
            "wsLobby": ContarConexoesWsLobby(),
            "salasAtivas": SalasAtivas,
            "filaRanqueada": FilaRanqueada,
            "filaEsperaConexao": Espera,
        },
        "aviso": Aviso,
    }
