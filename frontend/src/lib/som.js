/** Áudio do jogo (OGG Kenney CC0 em /public/sounds). */

function lerPrefs() {
  try {
    const P = JSON.parse(localStorage.getItem("termoPrefs") || "{}");
    if (P.som === undefined) P.som = true;
    if (P.volume === undefined) P.volume = 0.75;
    return P;
  } catch {
    return { som: true, volume: 0.75 };
  }
}

const ARQUIVOS = {
  tecla: "/sounds/tecla.ogg",
  apagar: "/sounds/apagar.ogg",
  chute: "/sounds/chute.ogg",
  acerto: "/sounds/acerto.ogg",
  vitoria: "/sounds/vitoria.ogg",
  erro: "/sounds/erro.ogg",
  entrada: "/sounds/entrada.ogg",
  chat: "/sounds/chat.ogg",
};

const GANHOS = {
  tecla: 0.55,
  apagar: 0.5,
  chute: 0.65,
  acerto: 0.75,
  vitoria: 0.85,
  erro: 0.7,
  entrada: 0.6,
  chat: 0.45,
};

const cache = new Map();
let desbloqueado = false;

function volumeUsuario() {
  const v = lerPrefs().volume;
  return typeof v === "number" && v >= 0 && v <= 1 ? v : 0.75;
}

function somLigado() {
  return lerPrefs().som !== false;
}

function criarAudio(tipo) {
  const src = ARQUIVOS[tipo];
  if (!src) return null;
  const a = new Audio(src);
  a.preload = "auto";
  return a;
}

function obterInstancia(tipo) {
  if (!cache.has(tipo)) cache.set(tipo, criarAudio(tipo));
  return cache.get(tipo);
}

export function prepararSons() {
  if (!somLigado()) return;
  Object.keys(ARQUIVOS).forEach((t) => {
    const a = obterInstancia(t);
    if (a) a.load();
  });
}

export function desbloquearAudio() {
  if (desbloqueado) return;
  desbloqueado = true;
  prepararSons();
  if (!somLigado()) return;
  const a = obterInstancia("tecla");
  if (!a) return;
  const s = a.cloneNode();
  s.volume = 0.001;
  s.play()
    .then(() => {
      s.pause();
      s.currentTime = 0;
    })
    .catch(() => {});
}

export function TocarSom(tipo, opts = {}) {
  if (!opts.forcar && !somLigado()) return;
  const base = obterInstancia(tipo);
  if (!base) return;

  const vol = (opts.volume ?? volumeUsuario()) * (GANHOS[tipo] ?? 0.6);
  const audio = base.cloneNode();
  audio.volume = Math.min(1, Math.max(0, vol));

  const play = () => {
    audio.play().catch(() => {});
  };

  if (!desbloqueado) {
    desbloquearAudio();
    play();
    return;
  }
  play();

  if (tipo === "erro" && navigator.vibrate) navigator.vibrate(30);
}
