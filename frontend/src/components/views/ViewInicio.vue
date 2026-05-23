<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import PainelHomeExtras from "../home/PainelHomeExtras.vue";
import HeroJogoAtivo from "../home/HeroJogoAtivo.vue";
import BtnInstalarPwa from "../home/BtnInstalarPwa.vue";

const store = useTermoStore();

const diariaBloqueada = computed(
  () => !store.contaRegistrada && !store.diariaFeita
);
</script>

<template>
  <section class="view view-ativa">
    <div class="layout-inicio">
      <div class="inicio-hero inicio-hero-compacto">
        <h1 class="hero-titulo">Descubra a palavra. <span>Em português.</span></h1>
      </div>

      <HeroJogoAtivo />

      <div class="inicio-tres-modos">
        <article
          class="modo-card modo-card-principal modo-diaria"
          :class="{
            'diaria-feita': store.diariaFeita && store.contaRegistrada,
            'modo-requer-conta': diariaBloqueada,
          }"
        >
          <span class="modo-badge">{{ store.diariaBadge }}</span>
          <h2>Palavra do dia</h2>

          <template v-if="diariaBloqueada">
            <p class="modo-explicacao">
              Todo dia uma palavra igual para quem joga no Brasil. Até 6 tentativas,
              <strong>uma partida por conta</strong>. O resultado entra no seu perfil,
              dá XP, badges e aparece no ranking da diária.
            </p>
            <p class="modo-explicacao modo-explicacao-sec">
              Visitante não conta — entre ou crie conta para jogar.
            </p>
            <div class="modo-acoes-conta">
              <button
                type="button"
                class="btn-modo btn-largo"
                @click="store.abrirLoginConta()"
              >
                Entrar
              </button>
              <button
                type="button"
                class="btn-modo btn-modo-sec btn-largo"
                @click="store.abrirCriarConta()"
              >
                Criar conta
              </button>
            </div>
          </template>

          <template v-else>
            <p>Uma palavra para todos. Jogue uma vez por dia.</p>
            <p class="diaria-contador">{{ store.proximaDiariaTexto }}</p>
            <div class="diaria-acoes">
              <button
                v-if="!store.diariaFeita"
                type="button"
                class="btn-modo btn-largo"
                @click="store.iniciarModo('diaria')"
              >
                {{ store.diariaBtnTexto }}
              </button>
              <template v-else>
                <button
                  type="button"
                  class="btn-modo btn-largo btn-destaque"
                  @click="store.verResultadoDiaria()"
                >
                  Ver resultado de hoje
                </button>
                <p class="diaria-feita-hint">Você já jogou a palavra de hoje.</p>
              </template>
            </div>
          </template>
        </article>

        <article class="modo-card modo-card-principal modo-jogar">
          <h2>Jogar</h2>
          <p>Prática, dueto, quarteto, ranqueado 1v1 e desafio.</p>
          <button
            type="button"
            class="btn-modo btn-modo-destaque btn-largo"
            @click="store.abrirDialog('jogar')"
          >
            Escolher modo
          </button>
        </article>

        <article class="modo-card modo-card-principal modo-arena-card">
          <h2>Arena</h2>
          <p>Salas online com amigos — até 8 jogadores.</p>
          <div class="arena-acoes-compacta">
            <button
              type="button"
              class="btn-modo btn-largo"
              @click="store.abrirDialog('criarSala')"
            >
              Criar sala
            </button>
            <div class="arena-entrar-linha">
              <input
                v-model="store.codigoEntrada"
                type="text"
                maxlength="6"
                placeholder="Código"
                class="input-redondo input-codigo"
                @input="store.codigoEntrada = store.codigoEntrada.toUpperCase()"
              />
              <button
                type="button"
                class="btn-modo btn-modo-sec"
                @click="store.entrarSala()"
              >
                Entrar
              </button>
            </div>
            <input
              v-model="store.senhaEntrada"
              type="text"
              maxlength="8"
              placeholder="Senha (opcional)"
              class="input-redondo input-senha input-senha-compacta"
            />
            <label class="toggle toggle-compact">
              <input v-model="store.espectadorEntrada" type="checkbox" />
              <span class="toggle-ui" />
              <span>Espectador</span>
            </label>
          </div>
        </article>
      </div>

      <PainelHomeExtras />

      <BtnInstalarPwa />
    </div>
  </section>
</template>
