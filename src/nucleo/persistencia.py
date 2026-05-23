import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path

import os

DiretorioDados = Path(os.environ.get("TERM0_DATA", Path(__file__).resolve().parent.parent.parent / "data"))
CaminhoBanco = DiretorioDados / "termo.db"


@contextmanager
def Conexao():
    DiretorioDados.mkdir(parents=True, exist_ok=True)
    Con = sqlite3.connect(CaminhoBanco)
    Con.row_factory = sqlite3.Row
    try:
        yield Con
        Con.commit()
    finally:
        Con.close()


def InicializarBanco() -> None:
    with Conexao() as C:
        C.executescript(
            """
            CREATE TABLE IF NOT EXISTS partidas_solo (
                id_partida TEXT PRIMARY KEY,
                palavra_secreta TEXT NOT NULL,
                palavra_com_acento TEXT NOT NULL,
                modo TEXT NOT NULL,
                data_dia TEXT,
                tentativas_json TEXT NOT NULL DEFAULT '[]',
                encerrada INTEGER NOT NULL DEFAULT 0,
                venceu INTEGER NOT NULL DEFAULT 0,
                nome_jogador TEXT,
                atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS ranking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_jogador TEXT NOT NULL,
                pontos INTEGER NOT NULL,
                modo TEXT NOT NULL,
                tentativas_usadas INTEGER NOT NULL,
                venceu INTEGER NOT NULL,
                data_hora TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_ranking_pontos ON ranking (pontos DESC);

            CREATE TABLE IF NOT EXISTS diaria_jogadores (
                nick TEXT NOT NULL,
                data_dia TEXT NOT NULL,
                venceu INTEGER NOT NULL,
                tentativas_usadas INTEGER NOT NULL,
                grade_texto TEXT,
                pontos INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (nick, data_dia)
            );

            CREATE TABLE IF NOT EXISTS salas (
                codigo_sala TEXT PRIMARY KEY,
                dados_json TEXT NOT NULL,
                atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS contas (
                id TEXT PRIMARY KEY,
                nick TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                senha_salt TEXT NOT NULL,
                eh_visitante INTEGER NOT NULL DEFAULT 0,
                pontos_ranqueada INTEGER NOT NULL DEFAULT 0,
                partidas_ranqueadas INTEGER NOT NULL DEFAULT 0,
                vitorias_ranqueadas INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_contas_pontos ON contas (pontos_ranqueada DESC);

            CREATE TABLE IF NOT EXISTS sessoes (
                token TEXT PRIMARY KEY,
                id_conta TEXT NOT NULL,
                expira_em TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (id_conta) REFERENCES contas(id)
            );

            CREATE TABLE IF NOT EXISTS historico_ranqueada (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_conta TEXT NOT NULL,
                id_oponente TEXT NOT NULL,
                codigo_sala TEXT,
                delta INTEGER NOT NULL,
                pontos_antes INTEGER NOT NULL,
                pontos_depois INTEGER NOT NULL,
                venceu INTEGER NOT NULL,
                data_hora TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        _AplicarMigracoesContas(C)
        _AplicarMigracoesProgresso(C)
        LimparRankingVisitantesEPontosZero()


def _AplicarMigracoesContas(C: sqlite3.Connection) -> None:
    Colunas = {Linha[1] for Linha in C.execute("PRAGMA table_info(contas)").fetchall()}
    if "email" not in Colunas:
        C.execute("ALTER TABLE contas ADD COLUMN email TEXT")
    C.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_contas_email
        ON contas (email) WHERE email IS NOT NULL AND email != ''
        """
    )
    C.execute(
        """
        UPDATE contas
        SET pontos_ranqueada = 0
        WHERE partidas_ranqueadas = 0 AND pontos_ranqueada = 1000
        """
    )
    if "avatar_id" not in Colunas:
        C.execute("ALTER TABLE contas ADD COLUMN avatar_id TEXT")
    if "ultima_atividade_em" not in Colunas:
        C.execute("ALTER TABLE contas ADD COLUMN ultima_atividade_em TEXT")
        C.execute(
            """
            UPDATE contas
            SET ultima_atividade_em = COALESCE(criado_em, datetime('now'))
            WHERE ultima_atividade_em IS NULL
            """
        )


def _AplicarMigracoesProgresso(C: sqlite3.Connection) -> None:
    Colunas = {Linha[1] for Linha in C.execute("PRAGMA table_info(contas)").fetchall()}
    if "xp_total" not in Colunas:
        C.execute("ALTER TABLE contas ADD COLUMN xp_total INTEGER NOT NULL DEFAULT 0")
    if "nivel" not in Colunas:
        C.execute("ALTER TABLE contas ADD COLUMN nivel INTEGER NOT NULL DEFAULT 1")

    ColunasDiaria = {
        Linha[1] for Linha in C.execute("PRAGMA table_info(diaria_jogadores)").fetchall()
    }
    if "id_conta" not in ColunasDiaria:
        C.execute("ALTER TABLE diaria_jogadores ADD COLUMN id_conta TEXT")

    ColunasPartida = {
        Linha[1] for Linha in C.execute("PRAGMA table_info(partidas_solo)").fetchall()
    }
    if "id_conta" not in ColunasPartida:
        C.execute("ALTER TABLE partidas_solo ADD COLUMN id_conta TEXT")
    if "token_partida" not in ColunasPartida:
        C.execute("ALTER TABLE partidas_solo ADD COLUMN token_partida TEXT")

    C.executescript(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_diaria_conta_dia
        ON diaria_jogadores (id_conta, data_dia)
        WHERE id_conta IS NOT NULL AND id_conta != '';

        CREATE TABLE IF NOT EXISTS diaria_sessao (
            id_conta TEXT NOT NULL,
            data_dia TEXT NOT NULL,
            id_partida TEXT NOT NULL,
            encerrada INTEGER NOT NULL DEFAULT 0,
            criado_em TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (id_conta, data_dia)
        );

        CREATE TABLE IF NOT EXISTS diaria_xp_tentativa (
            id_conta TEXT NOT NULL,
            data_dia TEXT NOT NULL,
            indice_tentativa INTEGER NOT NULL,
            PRIMARY KEY (id_conta, data_dia, indice_tentativa)
        );

        CREATE TABLE IF NOT EXISTS diaria_xp_conclusao (
            id_conta TEXT NOT NULL,
            data_dia TEXT NOT NULL,
            PRIMARY KEY (id_conta, data_dia)
        );

        CREATE TABLE IF NOT EXISTS conta_badges (
            id_conta TEXT NOT NULL,
            badge_id TEXT NOT NULL,
            desbloqueado_em TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (id_conta, badge_id)
        );

        CREATE TABLE IF NOT EXISTS xp_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_conta TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            motivo TEXT NOT NULL,
            data_hora TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS xp_ganho_diario (
            id_conta TEXT NOT NULL,
            data_dia TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (id_conta, data_dia)
        );

        CREATE TABLE IF NOT EXISTS arena_xp_rodada (
            id_conta TEXT NOT NULL,
            codigo_sala TEXT NOT NULL,
            numero_rodada INTEGER NOT NULL,
            PRIMARY KEY (id_conta, codigo_sala, numero_rodada)
        );

        CREATE TABLE IF NOT EXISTS arena_xp_sessao (
            id_conta TEXT NOT NULL,
            codigo_sala TEXT NOT NULL,
            PRIMARY KEY (id_conta, codigo_sala)
        );

        CREATE TABLE IF NOT EXISTS meta_semanal_progresso (
            id_conta TEXT NOT NULL,
            semana_iso TEXT NOT NULL,
            meta_id TEXT NOT NULL,
            progresso INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (id_conta, semana_iso, meta_id)
        );

        CREATE TABLE IF NOT EXISTS meta_semanal_recompensa (
            id_conta TEXT NOT NULL,
            semana_iso TEXT NOT NULL,
            meta_id TEXT NOT NULL,
            recompensado_em TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (id_conta, semana_iso, meta_id)
        );
        """
    )


def _SerializarEstadoPartida(Partida) -> str:
    Tabuleiros = getattr(Partida, "Tabuleiros", None)
    if Tabuleiros and len(Tabuleiros) > 1:
        return json.dumps(
            {
                "v": 2,
                "tabuleiros": Tabuleiros,
                "tentativas": Partida.Tentativas,
                "dificuldade": getattr(Partida, "Dificuldade", "normal"),
                "codigoDesafio": getattr(Partida, "CodigoDesafio", None),
            },
            ensure_ascii=False,
        )
    return json.dumps(Partida.Tentativas, ensure_ascii=False)


def _AplicarMetadadosPartidaLinha(Partida, Linha) -> None:
    Partida.NomeJogador = Linha["nome_jogador"] or "Jogador"
    Chaves = Linha.keys() if hasattr(Linha, "keys") else []
    if "id_conta" in Chaves:
        Partida.IdConta = Linha["id_conta"]
    if "token_partida" in Chaves:
        Partida.TokenPartida = Linha["token_partida"]


def _DesserializarEstadoPartida(Linha, ClassePartida):
    Bruto = json.loads(Linha["tentativas_json"])
    if isinstance(Bruto, dict) and Bruto.get("v") == 2:
        Tab = Bruto.get("tabuleiros", [])
        Partida = ClassePartida(
            IdPartida=Linha["id_partida"],
            PalavraSecreta=Tab[0]["palavraSecreta"] if Tab else Linha["palavra_secreta"],
            PalavraComAcento=Tab[0]["palavraComAcento"] if Tab else Linha["palavra_com_acento"],
            Modo=Linha["modo"],
            DataDia=Linha["data_dia"],
            Tentativas=Bruto.get("tentativas", []),
            Encerrada=bool(Linha["encerrada"]),
            Venceu=bool(Linha["venceu"]),
        )
        Partida.Tabuleiros = Tab
        Partida.Dificuldade = Bruto.get("dificuldade", "normal")
        Partida.CodigoDesafio = Bruto.get("codigoDesafio")
        _AplicarMetadadosPartidaLinha(Partida, Linha)
        return Partida
    Partida = ClassePartida(
        IdPartida=Linha["id_partida"],
        PalavraSecreta=Linha["palavra_secreta"],
        PalavraComAcento=Linha["palavra_com_acento"],
        Modo=Linha["modo"],
        DataDia=Linha["data_dia"],
        Tentativas=Bruto if isinstance(Bruto, list) else [],
        Encerrada=bool(Linha["encerrada"]),
        Venceu=bool(Linha["venceu"]),
    )
    _AplicarMetadadosPartidaLinha(Partida, Linha)
    return Partida


def SalvarPartidaSolo(Partida) -> None:
    Tabuleiros = getattr(Partida, "Tabuleiros", None)
    if Tabuleiros:
        Partida.PalavraSecreta = Tabuleiros[0]["palavraSecreta"]
        Partida.PalavraComAcento = Tabuleiros[0]["palavraComAcento"]
    with Conexao() as C:
        C.execute(
            """
            INSERT INTO partidas_solo (
                id_partida, palavra_secreta, palavra_com_acento, modo, data_dia,
                tentativas_json, encerrada, venceu, nome_jogador, id_conta,
                token_partida, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id_partida) DO UPDATE SET
                tentativas_json = excluded.tentativas_json,
                encerrada = excluded.encerrada,
                venceu = excluded.venceu,
                nome_jogador = excluded.nome_jogador,
                id_conta = COALESCE(excluded.id_conta, partidas_solo.id_conta),
                token_partida = COALESCE(partidas_solo.token_partida, excluded.token_partida),
                atualizado_em = datetime('now')
            """,
            (
                Partida.IdPartida,
                Partida.PalavraSecreta,
                Partida.PalavraComAcento,
                Partida.Modo,
                Partida.DataDia,
                _SerializarEstadoPartida(Partida),
                int(Partida.Encerrada),
                int(Partida.Venceu),
                getattr(Partida, "NomeJogador", None),
                getattr(Partida, "IdConta", None),
                getattr(Partida, "TokenPartida", None),
            ),
        )


def CarregarPartidaSolo(IdPartida: str, ClassePartida):
    with Conexao() as C:
        Linha = C.execute(
            "SELECT * FROM partidas_solo WHERE id_partida = ?", (IdPartida,)
        ).fetchone()
    if not Linha:
        return None
    return _DesserializarEstadoPartida(Linha, ClassePartida)


INATIVIDADE_VISITANTE_HORAS = 1


def _ParsearInstanteUtc(Texto: str | None):
    from datetime import datetime, timezone

    if not Texto:
        return None
    Valor = str(Texto).strip().replace("Z", "+00:00")
    try:
        Instante = datetime.fromisoformat(Valor)
    except ValueError:
        return None
    if Instante.tzinfo is None:
        Instante = Instante.replace(tzinfo=timezone.utc)
    return Instante


def VisitanteEstaInativo(Conta: dict) -> bool:
    from datetime import datetime, timedelta, timezone

    if not Conta.get("eh_visitante"):
        return False
    Ref = Conta.get("ultima_atividade_em") or Conta.get("criado_em")
    Instante = _ParsearInstanteUtc(Ref)
    if not Instante:
        return False
    Limite = datetime.now(timezone.utc) - timedelta(hours=INATIVIDADE_VISITANTE_HORAS)
    return Instante < Limite


def NickEhVisitante(Nick: str) -> bool:
    NickNorm = (Nick or "").strip()[:24].lower()
    if not NickNorm:
        return False
    Conta = ObterContaPorNick(NickNorm)
    return bool(
        Conta
        and Conta.get("eh_visitante")
        and not VisitanteEstaInativo(Conta)
    )


def LimparRankingVisitantesEPontosZero() -> None:
    with Conexao() as C:
        C.execute(
            """
            DELETE FROM ranking
            WHERE pontos <= 0
               OR LOWER(nome_jogador) IN (
                    SELECT LOWER(nick) FROM contas WHERE eh_visitante = 1
               )
            """
        )


def InserirRanking(
    NomeJogador: str,
    Pontos: int,
    Modo: str,
    TentativasUsadas: int,
    Venceu: bool,
    DataHora: str,
) -> None:
    with Conexao() as C:
        C.execute(
            """
            INSERT INTO ranking (nome_jogador, pontos, modo, tentativas_usadas, venceu, data_hora)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (NomeJogador, Pontos, Modo, TentativasUsadas, int(Venceu), DataHora),
        )
        C.execute(
            """
            DELETE FROM ranking WHERE id NOT IN (
                SELECT id FROM ranking ORDER BY pontos DESC LIMIT 50
            )
            """
        )


def ListarRanking(Limite: int = 20) -> list[dict]:
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT nome_jogador, pontos, modo, tentativas_usadas, venceu, data_hora
            FROM ranking ORDER BY pontos DESC LIMIT ?
            """,
            (Limite,),
        ).fetchall()
    return [dict(L) for L in Linhas]


def JaJogouDiaria(Nick: str, DataDia: str | None = None) -> bool:
    Data = DataDia or date.today().isoformat()
    NickNorm = Nick.strip()[:24].lower() or "jogador"
    with Conexao() as C:
        Linha = C.execute(
            "SELECT 1 FROM diaria_jogadores WHERE nick = ? AND data_dia = ?",
            (NickNorm, Data),
        ).fetchone()
    return Linha is not None


def JaJogouDiariaConta(IdConta: str, DataDia: str | None = None) -> bool:
    if not IdConta:
        return False
    Data = DataDia or date.today().isoformat()
    with Conexao() as C:
        Linha = C.execute(
            "SELECT 1 FROM diaria_jogadores WHERE id_conta = ? AND data_dia = ?",
            (IdConta, Data),
        ).fetchone()
    return Linha is not None


def JaConcluiuDiariaHoje(IdConta: str | None, Nick: str, DataDia: str) -> bool:
    if IdConta and JaJogouDiariaConta(IdConta, DataDia):
        return True
    return JaJogouDiaria(Nick, DataDia)


def ObterDiariaJogadorPorConta(IdConta: str, DataDia: str | None = None) -> dict | None:
    if not IdConta:
        return None
    Data = DataDia or date.today().isoformat()
    with Conexao() as C:
        Linha = C.execute(
            "SELECT * FROM diaria_jogadores WHERE id_conta = ? AND data_dia = ?",
            (IdConta, Data),
        ).fetchone()
    return dict(Linha) if Linha else None


def ObterDiariaJogador(Nick: str, DataDia: str | None = None) -> dict | None:
    Data = DataDia or date.today().isoformat()
    NickNorm = Nick.strip()[:24].lower() or "jogador"
    with Conexao() as C:
        Linha = C.execute(
            "SELECT * FROM diaria_jogadores WHERE nick = ? AND data_dia = ?",
            (NickNorm, Data),
        ).fetchone()
    return dict(Linha) if Linha else None


def AtualizarGradeDiariaConta(IdConta: str, DataDia: str, GradeTexto: str) -> bool:
    """Atualiza só o texto compartilhável da diária já concluída pela conta."""
    if not IdConta or not GradeTexto:
        return False
    with Conexao() as C:
        Cursor = C.execute(
            """
            UPDATE diaria_jogadores SET grade_texto = ?
            WHERE id_conta = ? AND data_dia = ?
            """,
            (GradeTexto[:4000], IdConta, DataDia),
        )
        return Cursor.rowcount > 0


def RegistrarDiaria(
    Nick: str,
    DataDia: str,
    Venceu: bool,
    TentativasUsadas: int,
    Pontos: int,
    GradeTexto: str | None = None,
    IdConta: str | None = None,
) -> None:
    NickNorm = Nick.strip()[:24].lower() or "jogador"
    with Conexao() as C:
        if IdConta:
            Existe = C.execute(
                "SELECT 1 FROM diaria_jogadores WHERE id_conta = ? AND data_dia = ?",
                (IdConta, DataDia),
            ).fetchone()
            if Existe:
                C.execute(
                    """
                    UPDATE diaria_jogadores SET
                        venceu = ?, tentativas_usadas = ?, grade_texto = ?, pontos = ?, nick = ?
                    WHERE id_conta = ? AND data_dia = ?
                    """,
                    (
                        int(Venceu),
                        TentativasUsadas,
                        GradeTexto,
                        Pontos,
                        NickNorm,
                        IdConta,
                        DataDia,
                    ),
                )
            else:
                C.execute(
                    """
                    INSERT INTO diaria_jogadores (
                        nick, data_dia, venceu, tentativas_usadas, grade_texto, pontos, id_conta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        NickNorm,
                        DataDia,
                        int(Venceu),
                        TentativasUsadas,
                        GradeTexto,
                        Pontos,
                        IdConta,
                    ),
                )
        else:
            C.execute(
                """
                INSERT INTO diaria_jogadores (nick, data_dia, venceu, tentativas_usadas, grade_texto, pontos)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(nick, data_dia) DO UPDATE SET
                    venceu = excluded.venceu,
                    tentativas_usadas = excluded.tentativas_usadas,
                    grade_texto = excluded.grade_texto,
                    pontos = excluded.pontos
                """,
                (NickNorm, DataDia, int(Venceu), TentativasUsadas, GradeTexto, Pontos),
            )
        if IdConta:
            C.execute(
                """
                UPDATE diaria_sessao SET encerrada = 1
                WHERE id_conta = ? AND data_dia = ?
                """,
                (IdConta, DataDia),
            )


def IniciarSessaoDiariaConta(IdConta: str, DataDia: str, IdPartida: str) -> None:
    with Conexao() as C:
        Antiga = C.execute(
            "SELECT encerrada FROM diaria_sessao WHERE id_conta = ? AND data_dia = ?",
            (IdConta, DataDia),
        ).fetchone()
        if Antiga and not Antiga["encerrada"]:
            C.execute(
                """
                UPDATE diaria_sessao SET id_partida = ? WHERE id_conta = ? AND data_dia = ?
                """,
                (IdPartida, IdConta, DataDia),
            )
            return
        if Antiga:
            return
        C.execute(
            """
            INSERT INTO diaria_sessao (id_conta, data_dia, id_partida, encerrada)
            VALUES (?, ?, ?, 0)
            """,
            (IdConta, DataDia, IdPartida),
        )


def ObterSessaoDiariaConta(IdConta: str, DataDia: str) -> dict | None:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT * FROM diaria_sessao WHERE id_conta = ? AND data_dia = ?",
            (IdConta, DataDia),
        ).fetchone()
    return dict(Linha) if Linha else None


def RegistrarXpDiariaTentativa(
    IdConta: str, DataDia: str, IdPartida: str, IndiceTentativa: int
) -> bool:
    Sessao = ObterSessaoDiariaConta(IdConta, DataDia)
    if not Sessao or Sessao.get("encerrada"):
        return False
    if Sessao.get("id_partida") != IdPartida:
        return False
    with Conexao() as C:
        try:
            C.execute(
                """
                INSERT INTO diaria_xp_tentativa (id_conta, data_dia, indice_tentativa)
                VALUES (?, ?, ?)
                """,
                (IdConta, DataDia, IndiceTentativa),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def MarcarDiariaXpConclusao(IdConta: str, DataDia: str) -> bool:
    with Conexao() as C:
        try:
            C.execute(
                "INSERT INTO diaria_xp_conclusao (id_conta, data_dia) VALUES (?, ?)",
                (IdConta, DataDia),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def ObterXpConta(IdConta: str) -> int:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT xp_total FROM contas WHERE id = ?", (IdConta,)
        ).fetchone()
    return int(Linha["xp_total"]) if Linha else 0


def AdicionarXpConta(IdConta: str, Quantidade: int) -> int:
    with Conexao() as C:
        C.execute(
            "UPDATE contas SET xp_total = xp_total + ? WHERE id = ?",
            (Quantidade, IdConta),
        )
        Linha = C.execute("SELECT xp_total FROM contas WHERE id = ?", (IdConta,)).fetchone()
    return int(Linha["xp_total"]) if Linha else 0


def ObterXpGanhoDiario(IdConta: str, DataDia: str | None = None) -> int:
    if DataDia is None:
        from .tempo_brasil import DataHojeIsoBrasil

        Data = DataHojeIsoBrasil()
    else:
        Data = DataDia
    with Conexao() as C:
        Linha = C.execute(
            "SELECT quantidade FROM xp_ganho_diario WHERE id_conta = ? AND data_dia = ?",
            (IdConta, Data),
        ).fetchone()
    return int(Linha["quantidade"]) if Linha else 0


def RegistrarXpGanhoDiario(
    IdConta: str, Quantidade: int, DataDia: str | None = None
) -> int:
    if Quantidade <= 0:
        return ObterXpGanhoDiario(IdConta, DataDia)
    if DataDia is None:
        from .tempo_brasil import DataHojeIsoBrasil

        Data = DataHojeIsoBrasil()
    else:
        Data = DataDia
    with Conexao() as C:
        C.execute(
            """
            INSERT INTO xp_ganho_diario (id_conta, data_dia, quantidade)
            VALUES (?, ?, ?)
            ON CONFLICT(id_conta, data_dia) DO UPDATE SET
                quantidade = quantidade + excluded.quantidade
            """,
            (IdConta, Data, Quantidade),
        )
        Linha = C.execute(
            "SELECT quantidade FROM xp_ganho_diario WHERE id_conta = ? AND data_dia = ?",
            (IdConta, Data),
        ).fetchone()
    return int(Linha["quantidade"]) if Linha else 0


def RegistrarXpArenaRodada(
    IdConta: str, CodigoSala: str, NumeroRodada: int
) -> bool:
    with Conexao() as C:
        try:
            C.execute(
                """
                INSERT INTO arena_xp_rodada (id_conta, codigo_sala, numero_rodada)
                VALUES (?, ?, ?)
                """,
                (IdConta, CodigoSala, int(NumeroRodada)),
            )
            return True
        except Exception:
            return False


def RegistrarXpArenaSessao(IdConta: str, CodigoSala: str) -> bool:
    with Conexao() as C:
        try:
            C.execute(
                "INSERT INTO arena_xp_sessao (id_conta, codigo_sala) VALUES (?, ?)",
                (IdConta, CodigoSala),
            )
            return True
        except Exception:
            return False


def IncrementarMetaSemanal(
    IdConta: str, SemanaIso: str, MetaId: str, Quantidade: int, MetaMax: int
) -> int | None:
    with Conexao() as C:
        Linha = C.execute(
            """
            SELECT progresso FROM meta_semanal_progresso
            WHERE id_conta = ? AND semana_iso = ? AND meta_id = ?
            """,
            (IdConta, SemanaIso, MetaId),
        ).fetchone()
        Atual = int(Linha["progresso"]) if Linha else 0
        if Atual >= MetaMax:
            return None
        Novo = min(MetaMax, Atual + Quantidade)
        C.execute(
            """
            INSERT INTO meta_semanal_progresso (id_conta, semana_iso, meta_id, progresso)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id_conta, semana_iso, meta_id) DO UPDATE SET progresso = ?
            """,
            (IdConta, SemanaIso, MetaId, Novo, Novo),
        )
    return Novo


def ObterProgressoMetasSemana(IdConta: str, SemanaIso: str) -> dict[str, int]:
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT meta_id, progresso FROM meta_semanal_progresso
            WHERE id_conta = ? AND semana_iso = ?
            """,
            (IdConta, SemanaIso),
        ).fetchall()
    return {L["meta_id"]: int(L["progresso"]) for L in Linhas}


def ListarMetasSemanaisRecompensadas(IdConta: str, SemanaIso: str) -> set[str]:
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT meta_id FROM meta_semanal_recompensa
            WHERE id_conta = ? AND semana_iso = ?
            """,
            (IdConta, SemanaIso),
        ).fetchall()
    return {L["meta_id"] for L in Linhas}


def MarcarMetaSemanalRecompensada(IdConta: str, SemanaIso: str, MetaId: str) -> bool:
    with Conexao() as C:
        try:
            C.execute(
                """
                INSERT INTO meta_semanal_recompensa (id_conta, semana_iso, meta_id)
                VALUES (?, ?, ?)
                """,
                (IdConta, SemanaIso, MetaId),
            )
            return True
        except Exception:
            return False


def ListarXpPorDia(IdConta: str, Dias: int = 7) -> list[dict]:
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT date(data_hora) AS dia, SUM(quantidade) AS xp
            FROM xp_log
            WHERE id_conta = ? AND data_hora >= datetime('now', ?)
            GROUP BY date(data_hora)
            ORDER BY dia ASC
            """,
            (IdConta, f"-{int(Dias)} days"),
        ).fetchall()
    return [{"data": L["dia"], "xp": int(L["xp"])} for L in Linhas]


def ListarDeltaRpPorDia(IdConta: str, Dias: int = 7) -> list[dict]:
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT date(data_hora) AS dia, SUM(delta) AS delta
            FROM historico_ranqueada
            WHERE id_conta = ? AND data_hora >= datetime('now', ?)
            GROUP BY date(data_hora)
            ORDER BY dia ASC
            """,
            (IdConta, f"-{int(Dias)} days"),
        ).fetchall()
    return [{"data": L["dia"], "deltaRp": int(L["delta"])} for L in Linhas]


def ContarSequenciaDiariasConcluidas(IdConta: str) -> int:
    from .tempo_brasil import DataHojeBrasil

    D = DataHojeBrasil()
    Sequencia = 0
    with Conexao() as C:
        for I in range(365):
            Dia = (D - timedelta(days=I)).isoformat()
            Linha = C.execute(
                """
                SELECT 1 FROM diaria_xp_conclusao
                WHERE id_conta = ? AND data_dia = ?
                UNION
                SELECT 1 FROM diaria_jogadores
                WHERE id_conta = ? AND data_dia = ?
                LIMIT 1
                """,
                (IdConta, Dia, IdConta, Dia),
            ).fetchone()
            if not Linha:
                break
            Sequencia += 1
    return Sequencia


def ContarRodadasArenaSemana(IdConta: str, SemanaIso: str) -> int:
    """Aproximação via progresso de meta (evita scan pesado)."""
    return ObterProgressoMetasSemana(IdConta, SemanaIso).get("arena_5", 0)


def RegistrarLogXp(IdConta: str, Quantidade: int, Motivo: str) -> None:
    with Conexao() as C:
        C.execute(
            "INSERT INTO xp_log (id_conta, quantidade, motivo) VALUES (?, ?, ?)",
            (IdConta, Quantidade, Motivo),
        )


def ListarBadgesConta(IdConta: str) -> list[str]:
    with Conexao() as C:
        Linhas = C.execute(
            "SELECT badge_id FROM conta_badges WHERE id_conta = ? ORDER BY desbloqueado_em",
            (IdConta,),
        ).fetchall()
    return [L["badge_id"] for L in Linhas]


def JaDesbloqueouBadge(IdConta: str, BadgeId: str) -> bool:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT 1 FROM conta_badges WHERE id_conta = ? AND badge_id = ?",
            (IdConta, BadgeId),
        ).fetchone()
    return Linha is not None


def DesbloquearBadge(IdConta: str, BadgeId: str) -> bool:
    if JaDesbloqueouBadge(IdConta, BadgeId):
        return False
    with Conexao() as C:
        try:
            C.execute(
                "INSERT INTO conta_badges (id_conta, badge_id) VALUES (?, ?)",
                (IdConta, BadgeId),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def ContarPartidasRanqueadasConta(IdConta: str) -> int:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT partidas_ranqueadas FROM contas WHERE id = ?", (IdConta,)
        ).fetchone()
    return int(Linha["partidas_ranqueadas"]) if Linha else 0


def ContarVitoriasRanqueadasConta(IdConta: str) -> int:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT vitorias_ranqueadas FROM contas WHERE id = ?", (IdConta,)
        ).fetchone()
    return int(Linha["vitorias_ranqueadas"]) if Linha else 0


def ObterIdContaPartidaSolo(IdPartida: str) -> str | None:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT id_conta FROM partidas_solo WHERE id_partida = ?",
            (IdPartida,),
        ).fetchone()
    if Linha and Linha["id_conta"]:
        return str(Linha["id_conta"])
    return None


def SalvarSalaSnapshot(CodigoSala: str, Dados: dict) -> None:
    with Conexao() as C:
        C.execute(
            """
            INSERT INTO salas (codigo_sala, dados_json, atualizado_em)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(codigo_sala) DO UPDATE SET
                dados_json = excluded.dados_json,
                atualizado_em = datetime('now')
            """,
            (CodigoSala.upper(), json.dumps(Dados, ensure_ascii=False)),
        )


def CarregarSalaSnapshot(CodigoSala: str) -> dict | None:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT dados_json FROM salas WHERE codigo_sala = ?",
            (CodigoSala.upper(),),
        ).fetchone()
    if not Linha:
        return None
    return json.loads(Linha["dados_json"])


def RemoverSala(CodigoSala: str) -> None:
    with Conexao() as C:
        C.execute("DELETE FROM salas WHERE codigo_sala = ?", (CodigoSala.upper(),))


def ListarHistoricoDiariaPorConta(IdConta: str, Limite: int = 30) -> list[dict]:
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT data_dia, venceu, tentativas_usadas, grade_texto, pontos
            FROM diaria_jogadores
            WHERE id_conta = ?
            ORDER BY data_dia DESC
            LIMIT ?
            """,
            (IdConta, Limite),
        ).fetchall()
    return [
        {
            "dataDia": L["data_dia"],
            "venceu": bool(L["venceu"]),
            "tentativasUsadas": L["tentativas_usadas"],
            "gradeTexto": L.get("grade_texto"),
            "pontos": L["pontos"],
        }
        for L in Linhas
    ]


def ListarHistoricoDiaria(Nick: str, Limite: int = 30) -> list[dict]:
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT data_dia, venceu, tentativas_usadas, grade_texto, pontos
            FROM diaria_jogadores
            WHERE nick = ?
            ORDER BY data_dia DESC
            LIMIT ?
            """,
            (Nick, Limite),
        ).fetchall()
    return [
        {
            "dataDia": L["data_dia"],
            "venceu": bool(L["venceu"]),
            "tentativasUsadas": L["tentativas_usadas"],
            "gradeTexto": L.get("grade_texto"),
            "pontos": L["pontos"],
        }
        for L in Linhas
    ]


def CriarConta(
    Nick: str,
    senha_hash: str,
    senha_salt: str,
    EhVisitante: bool = False,
    Email: str | None = None,
) -> str:
    from datetime import datetime, timezone

    from .ranqueada import PONTOS_INICIAIS

    IdConta = str(uuid.uuid4())
    EmailNorm = (Email or "").strip().lower() or None
    Agora = datetime.now(timezone.utc).isoformat()
    with Conexao() as C:
        C.execute(
            """
            INSERT INTO contas (
                id, nick, email, senha_hash, senha_salt, eh_visitante,
                pontos_ranqueada, ultima_atividade_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                IdConta,
                Nick,
                EmailNorm,
                senha_hash,
                senha_salt,
                int(EhVisitante),
                PONTOS_INICIAIS,
                Agora,
            ),
        )
    return IdConta


def ObterContaPorId(IdConta: str) -> dict | None:
    with Conexao() as C:
        Linha = C.execute("SELECT * FROM contas WHERE id = ?", (IdConta,)).fetchone()
    return dict(Linha) if Linha else None


def ObterContaPorNick(Nick: str) -> dict | None:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT * FROM contas WHERE nick = ?", (Nick.lower(),)
        ).fetchone()
    return dict(Linha) if Linha else None


def AtualizarNickConta(IdConta: str, Nick: str) -> None:
    with Conexao() as C:
        C.execute(
            "UPDATE contas SET nick = ? WHERE id = ?",
            (Nick.lower(), IdConta),
        )


def AtualizarAvatarConta(IdConta: str, AvatarId: str) -> None:
    with Conexao() as C:
        C.execute(
            "UPDATE contas SET avatar_id = ? WHERE id = ?",
            (AvatarId, IdConta),
        )


def ObterContaPorEmail(Email: str) -> dict | None:
    E = Email.strip().lower()
    if not E:
        return None
    with Conexao() as C:
        Linha = C.execute(
            "SELECT * FROM contas WHERE email = ?", (E,)
        ).fetchone()
    return dict(Linha) if Linha else None


def CriarSessao(IdConta: str, ExpiraEm: datetime) -> str:
    Token = uuid.uuid4().hex + uuid.uuid4().hex
    with Conexao() as C:
        C.execute(
            "INSERT INTO sessoes (token, id_conta, expira_em) VALUES (?, ?, ?)",
            (Token, IdConta, ExpiraEm.isoformat()),
        )
    return Token


def ObterSessaoPorToken(Token: str) -> dict | None:
    with Conexao() as C:
        Linha = C.execute(
            "SELECT token, id_conta, expira_em FROM sessoes WHERE token = ?",
            (Token,),
        ).fetchone()
    return dict(Linha) if Linha else None


def RevogarSessao(Token: str) -> None:
    with Conexao() as C:
        C.execute("DELETE FROM sessoes WHERE token = ?", (Token,))


def AtualizarAtividadeConta(IdConta: str, Instante: str | None = None) -> None:
    from datetime import datetime, timezone

    if Instante is None:
        Instante = datetime.now(timezone.utc).isoformat()
    with Conexao() as C:
        C.execute(
            "UPDATE contas SET ultima_atividade_em = ? WHERE id = ?",
            (Instante, IdConta),
        )


def ExcluirConta(IdConta: str) -> None:
    """Remove conta e dados ligados (visitante inativo liberando nick)."""
    with Conexao() as C:
        C.execute("DELETE FROM sessoes WHERE id_conta = ?", (IdConta,))
        C.execute("DELETE FROM historico_ranqueada WHERE id_conta = ?", (IdConta,))
        C.execute(
            "DELETE FROM historico_ranqueada WHERE id_oponente = ?", (IdConta,)
        )
        for Tabela in (
            "diaria_xp_tentativa",
            "diaria_xp_conclusao",
            "diaria_sessao",
            "diaria_jogadores",
            "xp_ganho_diario",
            "arena_xp_rodada",
            "arena_xp_sessao",
            "meta_semanal_recompensa",
            "meta_semanal_progresso",
            "conta_badges",
            "xp_log",
        ):
            C.execute(f"DELETE FROM {Tabela} WHERE id_conta = ?", (IdConta,))
        C.execute("DELETE FROM partidas_solo WHERE id_conta = ?", (IdConta,))
        C.execute("DELETE FROM contas WHERE id = ?", (IdConta,))


def AtualizarPontosRanqueada(IdConta: str, Pontos: int) -> None:
    with Conexao() as C:
        C.execute(
            """
            UPDATE contas SET
                pontos_ranqueada = ?,
                partidas_ranqueadas = partidas_ranqueadas + 1
            WHERE id = ?
            """,
            (Pontos, IdConta),
        )


def IncrementarVitoriaRanqueada(IdConta: str) -> None:
    with Conexao() as C:
        C.execute(
            "UPDATE contas SET vitorias_ranqueadas = vitorias_ranqueadas + 1 WHERE id = ?",
            (IdConta,),
        )


def RegistrarHistoricoRanqueada(
    IdConta: str,
    IdOponente: str,
    CodigoSala: str | None,
    Delta: int,
    PontosAntes: int,
    PontosDepois: int,
    Venceu: bool,
) -> None:
    with Conexao() as C:
        C.execute(
            """
            INSERT INTO historico_ranqueada (
                id_conta, id_oponente, codigo_sala, delta,
                pontos_antes, pontos_depois, venceu
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                IdConta,
                IdOponente,
                CodigoSala,
                Delta,
                PontosAntes,
                PontosDepois,
                int(Venceu),
            ),
        )
        if Venceu:
            C.execute(
                "UPDATE contas SET vitorias_ranqueadas = vitorias_ranqueadas + 1 WHERE id = ?",
                (IdConta,),
            )


def ListarRankingRanqueada(Limite: int = 50) -> list[dict]:
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT nick, pontos_ranqueada, partidas_ranqueadas, vitorias_ranqueadas, eh_visitante
            FROM contas
            WHERE eh_visitante = 0 AND partidas_ranqueadas > 0
            ORDER BY pontos_ranqueada DESC
            LIMIT ?
            """,
            (Limite,),
        ).fetchall()
    return [dict(L) for L in Linhas]


def ListarContasRanqueamento() -> list[dict]:
    """Todas as contas registradas (não visitante) para o ranking global."""
    with Conexao() as C:
        Linhas = C.execute(
            """
            SELECT nick, pontos_ranqueada, partidas_ranqueadas, vitorias_ranqueadas
            FROM contas
            WHERE eh_visitante = 0
            ORDER BY pontos_ranqueada DESC
            """
        ).fetchall()
    return [dict(L) for L in Linhas]


def ListarSalasAtivas() -> list[str]:
    with Conexao() as C:
        Linhas = C.execute("SELECT codigo_sala, dados_json FROM salas").fetchall()
    Codigos = []
    for L in Linhas:
        try:
            D = json.loads(L["dados_json"])
            if not D.get("partidaEncerrada") and D.get("estadoSala") != "encerrada":
                Codigos.append(L["codigo_sala"])
        except json.JSONDecodeError:
            continue
    return Codigos
