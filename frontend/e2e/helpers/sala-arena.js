import { expect } from "@playwright/test";

const CHAVE_NICK = "termoNick";
const CHAVE_SESSAO = "termoSessao";
const CHAVE_CODIGO = "termoCodigoSala";

export async function dispensarTutorial(page) {
  await page.evaluate(() => {
    localStorage.setItem("termoTutorialVisto", "1");
    localStorage.setItem("termoTutorialMultiVisto", "1");
  });
}

export async function definirNick(page, nick) {
  await page.goto("/");
  await page.evaluate(
    ([chave, valor]) => localStorage.setItem(chave, valor),
    [CHAVE_NICK, nick]
  );
  await dispensarTutorial(page);
  await page.reload();
  await dispensarTutorial(page);
}

export async function criarSalaViaApi(request, nick) {
  const R = await request.post("/api/sala/criar", {
    data: {
      nomeJogador: nick,
      maximoJogadores: 2,
      mesmaPalavra: true,
      inicioAutoDois: false,
      salaPublica: true,
    },
  });
  expect(R.ok()).toBeTruthy();
  return R.json();
}

export async function entrarSalaViaApi(request, codigoSala, nick) {
  const R = await request.post("/api/sala/entrar", {
    data: { codigoSala, nomeJogador: nick },
  });
  expect(R.ok()).toBeTruthy();
  return R.json();
}

export async function injetarSessaoArena(page, dados, nick) {
  await page.goto("/");
  await dispensarTutorial(page);
  await page.evaluate(
    ([nickChave, nick, codigoChave, sessaoChave, payload]) => {
      localStorage.setItem(nickChave, nick);
      localStorage.setItem(codigoChave, payload.codigoSala);
      localStorage.setItem(
        sessaoChave,
        JSON.stringify({
          arena: {
            codigoSala: payload.codigoSala,
            idJogador: payload.idJogador,
            souCriador: payload.souCriador,
            configuracao: payload.configuracao,
            view: "arenaLobby",
          },
        })
      );
    },
    [CHAVE_NICK, nick, CHAVE_CODIGO, CHAVE_SESSAO, dados]
  );
  await page.reload();
  await dispensarTutorial(page);
  await expect(page.locator(".lobby-codigo-grande")).toContainText(
    dados.codigoSala,
    { timeout: 20000 }
  );
}

export async function lobbyProntoEIniciar(host, guest) {
  await host.getByRole("button", { name: /Marcar pronto/i }).click();
  await guest.getByRole("button", { name: /Marcar pronto/i }).click();
  await host.getByRole("button", { name: "Iniciar partida" }).click();
  await expect(host.locator(".grade .linha").first()).toBeVisible({
    timeout: 25000,
  });
  await expect(guest.locator(".grade .linha").first()).toBeVisible({
    timeout: 25000,
  });
}

export async function digitarPalavra(page, palavra, { enviar = true } = {}) {
  for (const L of palavra.toLowerCase()) {
    await page.keyboard.press(L);
  }
  if (enviar) {
    await page.keyboard.press("Enter");
  }
}

export async function metaArena(page) {
  return page.evaluate((chave) => {
    try {
      const bruto = JSON.parse(localStorage.getItem(chave) || "{}");
      const arena = bruto.arena || bruto;
      return {
        codigoSala: arena.codigoSala || bruto.codigoSala,
        idJogador: arena.idJogador || bruto.idJogador,
      };
    } catch {
      return {};
    }
  }, CHAVE_SESSAO);
}

export async function tentativasUsadasApi(request, codigo, idJogador) {
  const R = await request.get(
    `/api/sala/${codigo}?id_jogador=${encodeURIComponent(idJogador)}`
  );
  expect(R.ok()).toBeTruthy();
  const D = await R.json();
  const eu = D.jogadores?.find((j) => j.souEu);
  return eu?.tentativasUsadas ?? eu?.tentativas?.length ?? 0;
}

export async function chuteInvalidoViaWs(page, palavra = "xxxxx") {
  return page.evaluate(async (p) => {
    const sessao = JSON.parse(localStorage.getItem("termoSessao") || "{}");
    const arena = sessao.arena || sessao;
    const codigo = arena.codigoSala;
    const id = arena.idJogador;
    if (!codigo || !id) return { erro: "sem sessão arena" };

    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${location.host}/ws/sala/${codigo}/${id}`;

    return new Promise((resolve) => {
      const ws = new WebSocket(url);
      const timer = setTimeout(
        () => resolve({ erro: "timeout ws" }),
        12000
      );
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.tipo === "chuteInvalido") {
            clearTimeout(timer);
            ws.close();
            resolve({ tipo: msg.tipo, mensagem: msg.mensagem });
          }
        } catch {
          /* ignora */
        }
      };
      ws.onopen = () => {
        ws.send(
          JSON.stringify({ tipo: "chute", dados: { palavra: p } })
        );
      };
      ws.onerror = () => {
        clearTimeout(timer);
        resolve({ erro: "erro ws" });
      };
    });
  }, palavra);
}

export async function prepararArenaDoisJogadores(browser, request, hostNick, guestNick) {
  const hostData = await criarSalaViaApi(request, hostNick);
  const guestData = await entrarSalaViaApi(
    request,
    hostData.codigoSala,
    guestNick
  );

  const hostCtx = await browser.newContext();
  const guestCtx = await browser.newContext();
  const host = await hostCtx.newPage();
  const guest = await guestCtx.newPage();

  await injetarSessaoArena(host, hostData, hostNick);
  await injetarSessaoArena(guest, guestData, guestNick);
  await lobbyProntoEIniciar(host, guest);

  return {
    host,
    guest,
    hostCtx,
    guestCtx,
    codigo: hostData.codigoSala,
    hostData,
    guestData,
  };
}

export async function iniciarPraticaViaApi(request, nick) {
  const R = await request.post("/api/jogar/iniciar", {
    data: { nomeJogador: nick, modo: "pratica" },
  });
  expect(R.ok()).toBeTruthy();
  return R.json();
}

export async function retomarPraticaNaPagina(page, partida, nick) {
  await page.goto("/");
  await dispensarTutorial(page);
  await page.evaluate(
    ([nickChave, nickVal, sessaoChave, solo]) => {
      localStorage.setItem(nickChave, nickVal);
      localStorage.setItem(sessaoChave, JSON.stringify({ solo }));
    },
    [
      CHAVE_NICK,
      nick,
      CHAVE_SESSAO,
      {
        modo: "pratica",
        idPartida: partida.idPartida,
        tokenPartida: partida.tokenPartida,
        tentativa: 0,
        letras: ["", "", "", "", ""],
        indiceCursor: 0,
        tentativasHist: [],
        teclado: {},
        maximoTentativas: partida.maximoTentativas || 6,
      },
    ]
  );
  await page.reload();
  await dispensarTutorial(page);
  await expect(page.locator(".grade .linha").first()).toBeVisible({
    timeout: 25000,
  });
}
