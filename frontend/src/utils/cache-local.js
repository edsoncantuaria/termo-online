import {
  CHAVE_SESSAO,
  CHAVE_CODIGO_SALA,
  CHAVE_STATS,
  CHAVE_TUTORIAL_VISTO,
  CHAVE_TUTORIAL_MULTI,
} from "./constantes.js";
import { LimparSessao } from "./sessao.js";

const CHAVE_HASH_DICIONARIO = "termoDicionarioHash";
const CHAVE_PALAVRAS_DICIONARIO = "termoDicionarioPalavras";

/** Remove cache de dicionário, sessão retomável, tutoriais e estatísticas locais. */
export function LimparCacheAplicacao() {
  LimparSessao();
  localStorage.removeItem(CHAVE_HASH_DICIONARIO);
  localStorage.removeItem(CHAVE_PALAVRAS_DICIONARIO);
  localStorage.removeItem(CHAVE_STATS);
  localStorage.removeItem(CHAVE_TUTORIAL_VISTO);
  localStorage.removeItem(CHAVE_TUTORIAL_MULTI);
  localStorage.removeItem(CHAVE_CODIGO_SALA);
}
