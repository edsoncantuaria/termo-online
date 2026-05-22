/** Catálogo de avatares — mesma família visual (rosto redondo + traço grosso). */

export const AVATAR_PADRAO = "folha";

export const AVATARES = [
  { id: "folha", nome: "Folha", corFundo: "#3d7a4a" },
  { id: "broto", nome: "Broto", corFundo: "#5fad62" },
  { id: "sol", nome: "Sol", corFundo: "#c9a227" },
  { id: "nuvem", nome: "Nuvem", corFundo: "#6b8cae" },
  { id: "cogumelo", nome: "Cogumelo", corFundo: "#b85c4a" },
  { id: "coruja", nome: "Coruja", corFundo: "#5c5668" },
  { id: "raposa", nome: "Raposa", corFundo: "#c4783a" },
  { id: "gato", nome: "Gato", corFundo: "#7a6b8a" },
  { id: "peixe", nome: "Peixe", corFundo: "#2d8a9a" },
  { id: "abelha", nome: "Abelha", corFundo: "#d4a82a" },
  { id: "tulipa", nome: "Tulipa", corFundo: "#c45c7a" },
  { id: "pinheiro", nome: "Pinheiro", corFundo: "#2d5c42" },
];

const IDS = new Set(AVATARES.map((a) => a.id));

export function AvatarValido(id) {
  return IDS.has(id);
}

export function AvatarPadraoDeNick(nick) {
  let h = 0;
  const s = (nick || "?").trim().toLowerCase();
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return AVATARES[h % AVATARES.length].id;
}

export function MetaAvatar(id) {
  return AVATARES.find((a) => a.id === id) || AVATARES[0];
}

const CHAVE_AVATAR_LOCAL = "termoAvatarId";

export function CarregarAvatarLocal() {
  try {
    const id = localStorage.getItem(CHAVE_AVATAR_LOCAL);
    return AvatarValido(id) ? id : null;
  } catch {
    return null;
  }
}

export function SalvarAvatarLocal(id) {
  if (AvatarValido(id)) localStorage.setItem(CHAVE_AVATAR_LOCAL, id);
  else localStorage.removeItem(CHAVE_AVATAR_LOCAL);
}

/** Avatar exibido: conta (servidor) → local (visitante) → derivado do nick. */
export function AvatarEfetivo(conta, nickFallback = "jogador") {
  if (conta?.avatarId && AvatarValido(conta.avatarId)) return conta.avatarId;
  const local = CarregarAvatarLocal();
  if (local) return local;
  return AvatarPadraoDeNick(conta?.nick || nickFallback);
}
