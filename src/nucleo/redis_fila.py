"""Fila ranqueada compartilhada via Redis (vários workers / instâncias)."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, fields

from .matchmaking import EntradaFila, FilaMatchmaking
from .redis_estado import AdquirirLockRedis, IdWorker, RedisHabilitado, _ObterCliente

Log = logging.getLogger("termo.redis_fila")

_PREFIXO = "termo:fila"
_CHAVE_ENTRADAS = f"{_PREFIXO}:entradas"
_CHAVE_REVANCHE = f"{_PREFIXO}:revanche"
_CHAVE_ULTIMO_MATCH = f"{_PREFIXO}:ultimo_match"
_CHAVE_ULTIMO_OPONENTE = f"{_PREFIXO}:ultimo_oponente"
_LOCK_PROCESSAR = f"{_PREFIXO}:lock_processar"
_TTL_AUX_SEG = 900


def FilaRedisDisponivel() -> bool:
    return RedisHabilitado() and _ObterCliente() is not None


def _SerializarEntrada(E: EntradaFila) -> str:
    return json.dumps(asdict(E), ensure_ascii=False)


def _DesserializarEntrada(Dados: str) -> EntradaFila:
    D = json.loads(Dados)
    Permitidos = {F.name for F in fields(EntradaFila)}
    return EntradaFila(**{K: V for K, V in D.items() if K in Permitidos})


class _MapaRedisEntradas:
    def __contains__(self, Chave: str) -> bool:
        Cliente = _ObterCliente()
        return bool(Cliente and Cliente.hexists(_CHAVE_ENTRADAS, Chave))

    def __getitem__(self, Chave: str) -> EntradaFila:
        Cliente = _ObterCliente()
        if not Cliente:
            raise KeyError(Chave)
        Bruto = Cliente.hget(_CHAVE_ENTRADAS, Chave)
        if not Bruto:
            raise KeyError(Chave)
        return _DesserializarEntrada(Bruto)

    def __setitem__(self, Chave: str, Valor: EntradaFila) -> None:
        Cliente = _ObterCliente()
        if Cliente:
            Cliente.hset(_CHAVE_ENTRADAS, Chave, _SerializarEntrada(Valor))

    def pop(self, Chave: str, Padrao=None):
        Cliente = _ObterCliente()
        if not Cliente:
            return Padrao
        Bruto = Cliente.hget(_CHAVE_ENTRADAS, Chave)
        if not Bruto:
            return Padrao
        Cliente.hdel(_CHAVE_ENTRADAS, Chave)
        return _DesserializarEntrada(Bruto)

    def keys(self):
        Cliente = _ObterCliente()
        if not Cliente:
            return []
        return list(Cliente.hkeys(_CHAVE_ENTRADAS))

    def values(self):
        return [self[K] for K in self.keys()]

    def __len__(self) -> int:
        Cliente = _ObterCliente()
        return int(Cliente.hlen(_CHAVE_ENTRADAS)) if Cliente else 0

    def get(self, Chave: str, Padrao=None):
        try:
            return self[Chave]
        except KeyError:
            return Padrao


class _MapaRedisStr:
    def __init__(self, ChaveHash: str) -> None:
        self._Chave = ChaveHash

    def __contains__(self, Chave: str) -> bool:
        Cliente = _ObterCliente()
        return bool(Cliente and Cliente.hexists(self._Chave, Chave))

    def __getitem__(self, Chave: str) -> str:
        Cliente = _ObterCliente()
        if not Cliente:
            raise KeyError(Chave)
        Valor = Cliente.hget(self._Chave, Chave)
        if Valor is None:
            raise KeyError(Chave)
        return Valor

    def __setitem__(self, Chave: str, Valor: str) -> None:
        Cliente = _ObterCliente()
        if Cliente:
            Cliente.hset(self._Chave, Chave, Valor)

    def pop(self, Chave: str, Padrao=None):
        Cliente = _ObterCliente()
        if not Cliente:
            return Padrao
        Pipe = Cliente.pipeline()
        Pipe.hget(self._Chave, Chave)
        Pipe.hdel(self._Chave, Chave)
        Valor, _ = Pipe.execute()
        return Valor if Valor is not None else Padrao

    def get(self, Chave: str, Padrao=None):
        Cliente = _ObterCliente()
        if not Cliente:
            return Padrao
        Valor = Cliente.hget(self._Chave, Chave)
        return Valor if Valor is not None else Padrao

    def items(self):
        Cliente = _ObterCliente()
        if not Cliente:
            return []
        return list(Cliente.hgetall(self._Chave).items())


class _MapaRedisJson:
    def __init__(self, ChaveHash: str) -> None:
        self._Chave = ChaveHash

    def __contains__(self, Chave: str) -> bool:
        Cliente = _ObterCliente()
        return bool(Cliente and Cliente.hexists(self._Chave, Chave))

    def get(self, Chave: str, Padrao=None):
        Cliente = _ObterCliente()
        if not Cliente:
            return Padrao
        Bruto = Cliente.hget(self._Chave, Chave)
        if not Bruto:
            return Padrao
        return json.loads(Bruto)

    def pop(self, Chave: str, Padrao=None):
        Cliente = _ObterCliente()
        if not Cliente:
            return Padrao
        Bruto = Cliente.hget(self._Chave, Chave)
        if not Bruto:
            return Padrao
        Cliente.hdel(self._Chave, Chave)
        return json.loads(Bruto)

    def __setitem__(self, Chave: str, Valor: dict) -> None:
        Cliente = _ObterCliente()
        if Cliente:
            Cliente.hset(self._Chave, Chave, json.dumps(Valor, ensure_ascii=False))
            Cliente.expire(self._Chave, _TTL_AUX_SEG)


class FilaMatchmakingRedis(FilaMatchmaking):
    """Mesma lógica da fila em memória; estado compartilhado no Redis."""

    def __init__(self) -> None:
        super().__init__()
        self.Fila = _MapaRedisEntradas()
        self.RevancheAlvo = _MapaRedisStr(_CHAVE_REVANCHE)
        self.UltimoMatch = _MapaRedisJson(_CHAVE_ULTIMO_MATCH)
        self.UltimoOponenteHumano = _MapaRedisJson(_CHAVE_ULTIMO_OPONENTE)

    def Processar(self, Gerenciador) -> None:
        # Bots/tempo na fila: sempre (poll do cliente não pode depender do lock).
        self._ProcessarBotsNaFila(Gerenciador)
        if not AdquirirLockRedis(_LOCK_PROCESSAR, Segundos=5):
            return
        self._TentarParearReais(Gerenciador)


def ConstruirFilaGlobal() -> FilaMatchmaking:
    import os

    if os.environ.get("TERM0_REDIS_FILA", "1").lower() in ("0", "false", "no"):
        return FilaMatchmaking()
    if FilaRedisDisponivel():
        Log.info("Fila ranqueada: Redis (worker %s).", IdWorker())
        return FilaMatchmakingRedis()
    return FilaMatchmaking()
