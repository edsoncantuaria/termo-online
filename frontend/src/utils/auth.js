const CHAVE_TOKEN = "termoToken";
const CHAVE_CONTA = "termoConta";

export function CarregarAuthLocal() {
  try {
    const token = localStorage.getItem(CHAVE_TOKEN);
    const conta = JSON.parse(localStorage.getItem(CHAVE_CONTA) || "null");
    return { token, conta };
  } catch {
    return { token: null, conta: null };
  }
}

export function SalvarAuthLocal(token, conta) {
  if (token) localStorage.setItem(CHAVE_TOKEN, token);
  else localStorage.removeItem(CHAVE_TOKEN);
  if (conta) localStorage.setItem(CHAVE_CONTA, JSON.stringify(conta));
  else localStorage.removeItem(CHAVE_CONTA);
}

export function LimparAuthLocal() {
  localStorage.removeItem(CHAVE_TOKEN);
  localStorage.removeItem(CHAVE_CONTA);
}

export function HeadersAuth(extra = {}) {
  const { token } = CarregarAuthLocal();
  const H = { ...extra };
  if (token) H.Authorization = `Bearer ${token}`;
  return H;
}
