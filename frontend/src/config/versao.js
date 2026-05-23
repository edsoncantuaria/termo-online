/**
 * Manter alinhado com src/nucleo/versao.py.
 *
 * Política: mudança significativa → +0.1 (1.1, 1.2…); marco grande → 2.0.
 */
export const VERSAO_NUMERO = "1.3.0";

/** Release: v1.3. Bugfix (patch > 0): v1.3.1 — igual a nucleo/versao.py */
function RotuloDeVersao(Numero) {
  const Partes = Numero.split(".");
  if (Partes.length >= 3) {
    const Patch = parseInt(Partes[2], 10);
    if (!Number.isNaN(Patch) && Patch > 0) {
      return `v${Partes[0]}.${Partes[1]}.${Partes[2]}`;
    }
  }
  if (Partes.length >= 2) return `v${Partes[0]}.${Partes[1]}`;
  return `v${Numero}`;
}

export const VERSAO_ROTULO = RotuloDeVersao(VERSAO_NUMERO);
