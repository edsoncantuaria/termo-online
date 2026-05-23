import { FormatarCronometro } from "./jogo.js";

export function NickExibicao(Nick) {
  const N = (Nick || "").trim().toLowerCase();
  if (!N) return "";
  const Partes = N.match(/^([a-z_]+)(\d*)$/);
  if (!Partes) return N;
  const Nome =
    Partes[1].charAt(0).toLocaleUpperCase("pt-BR") + Partes[1].slice(1);
  return Partes[2] ? `${Nome}${Partes[2]}` : Nome;
}

export function InicialNick(Nome) {
  const L = (NickExibicao(Nome) || "?").trim();
  if (!L) return "?";
  return [...L][0].toLocaleUpperCase("pt-BR");
}

export function CorAvatarNick(Nome) {
  let h = 0;
  const s = (Nome || "?").trim();
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  const matizes = [38, 82, 128, 168, 210, 268, 310];
  return `hsl(${matizes[h % matizes.length]} 42% 36%)`;
}

export function TextoStatusLobby(D) {
  const total = D.jogadores?.length || 0;
  const online =
    D.jogadoresOnline ??
    D.jogadores?.filter((j) => j.conectado !== false).length ??
    0;
  const max = D.configuracao?.maximoJogadores || 8;
  if (D.estadoSala === "jogando") return "Partida em andamento…";
  const prontos = D.prontosOnline ?? 0;
  const totalProntidao = D.totalProntidao ?? online;
  if (online < 2)
    return `Aguardando jogadores (${online} online · ${total}/${max})`;
  if (!D.todosProntos) {
    if (D.souCriador)
      return `${prontos}/${totalProntidao} prontos — aguarde todos (${total}/${max})`;
    return `${prontos}/${totalProntidao} prontos — marque quando estiver pronto`;
  }
  if (D.souCriador)
    return `Todos prontos — você pode iniciar (${total}/${max})`;
  return `${online} online — aguardando o host iniciar`;
}

export function StatusJogadorRodada(j, maxTentativas = 6) {
  if (j.modoCompetitivo && !j.espectador) {
    if (j.finalizou)
      return { texto: "Encerrou a rodada", classe: "status-fim" };
    const n =
      typeof j.tentativasUsadas === "number"
        ? j.tentativasUsadas
        : j.jaChutou
          ? 1
          : 0;
    if (n > 0) {
      return {
        texto: `Fez ${n} chute${n > 1 ? "s" : ""}`,
        classe: "status-jogando",
      };
    }
    return { texto: "Sem chute ainda", classe: "status-aguardo" };
  }
  if (j.espectador)
    return { texto: "Espectador", classe: "status-espectador" };
  if (j.venceu) return { texto: "Venceu a rodada", classe: "status-venceu" };
  if (j.tempoEsgotado)
    return { texto: "Tempo esgotado", classe: "status-tempo" };
  if (j.finalizou) return { texto: "Encerrou", classe: "status-fim" };
  if (j.segundosRestantes !== undefined) {
    return {
      texto: FormatarCronometro(j.segundosRestantes),
      classe: "status-timer",
    };
  }
  if (!j.tentativasUsadas)
    return { texto: "Aguardando chute…", classe: "status-jogando" };
  return {
    texto: `${j.tentativasUsadas}/${maxTentativas} tentativas`,
    classe: "status-jogando",
  };
}

export function ChipsConfigLobby(D) {
  const cfg = D.configuracao || {};
  return [
    cfg.mesmaPalavra ? "Mesma palavra" : "Palavras diferentes",
    cfg.verOutros ? "Ver tabuleiros" : "Modo discreto",
    `Até ${cfg.maximoJogadores || 8} jogadores`,
    cfg.modoSessaoTexto ||
      cfg.modoRodadasTexto ||
      D.modoSessaoTexto ||
      D.modoRodadasTexto ||
      "Maratona",
    cfg.tempoLimiteTexto || "Sem limite",
    D.temSenha ? "Com senha" : null,
    cfg.ranqueada ? "Melhor de 3" : null,
  ].filter(Boolean);
}
