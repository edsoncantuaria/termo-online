const CHAVE_TOKEN = "termoToken";
const CHAVE_CONTA = "termoConta";
const CHAVE_INSTANCIA = "termoInstancia";

export function CarregarAuthLocal() {
  try {
    const token = localStorage.getItem(CHAVE_TOKEN);
    const conta = JSON.parse(localStorage.getItem(CHAVE_CONTA) || "null");
    const instanciaCliente = localStorage.getItem(CHAVE_INSTANCIA);
    return { token, conta, instanciaCliente };
  } catch {
    return { token: null, conta: null, instanciaCliente: null };
  }
}

export function SalvarInstanciaLocal(instancia) {
  if (instancia) localStorage.setItem(CHAVE_INSTANCIA, instancia);
  else localStorage.removeItem(CHAVE_INSTANCIA);
}

export function SalvarAuthLocal(token, conta, instanciaCliente) {
  if (token) localStorage.setItem(CHAVE_TOKEN, token);
  else localStorage.removeItem(CHAVE_TOKEN);
  if (conta) localStorage.setItem(CHAVE_CONTA, JSON.stringify(conta));
  else localStorage.removeItem(CHAVE_CONTA);
  if (instanciaCliente !== undefined) {
    SalvarInstanciaLocal(instanciaCliente);
  }
}

export function LimparAuthLocal() {
  localStorage.removeItem(CHAVE_TOKEN);
  localStorage.removeItem(CHAVE_CONTA);
  localStorage.removeItem(CHAVE_INSTANCIA);
}

export function HeadersAuth(extra = {}) {
  const { token, instanciaCliente } = CarregarAuthLocal();
  const H = { ...extra };
  if (token) H.Authorization = `Bearer ${token}`;
  if (instanciaCliente) H["X-Termo-Instancia"] = instanciaCliente;
  return H;
}
