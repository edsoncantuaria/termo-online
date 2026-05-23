import { test, expect } from "@playwright/test";

test("conta registrada: segunda instância invalida a primeira (409)", async ({
  request,
}) => {
  const nick = `e2e_${Date.now().toString(36).slice(-6)}`;
  const email = `${nick}@e2e.test`;
  const senha = "senha12345";

  const reg = await request.post("/api/auth/registrar", {
    data: { nick, email, senha },
  });
  expect(reg.ok()).toBeTruthy();
  const { token: token1, instanciaCliente: inst1 } = await reg.json();

  const eu1 = await request.get("/api/auth/eu", {
    headers: {
      Authorization: `Bearer ${token1}`,
      "X-Termo-Instancia": inst1,
    },
  });
  expect(eu1.ok()).toBeTruthy();

  const login = await request.post("/api/auth/login", {
    data: { identificador: email, senha },
  });
  expect(login.ok()).toBeTruthy();
  const { instanciaCliente: inst2 } = await login.json();
  expect(inst2).not.toBe(inst1);

  const conflito = await request.get("/api/auth/eu", {
    headers: {
      Authorization: `Bearer ${token1}`,
      "X-Termo-Instancia": inst1,
    },
  });
  expect(conflito.status()).toBe(409);
  const corpo = await conflito.json();
  expect(corpo.detail).toMatch(/outro dispositivo|outra aba/i);
});
