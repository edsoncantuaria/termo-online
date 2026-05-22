<script setup>
import { useTermoStore } from "../../stores/termo.js";
import PainelHomeExtras from "../home/PainelHomeExtras.vue";

const store = useTermoStore();
</script>

<template>
  <section class="view view-ativa">
    <div class="layout-inicio">
      <div class="inicio-hero inicio-hero-compacto">
        <h1 class="hero-titulo">Descubra a palavra. <span>Em português.</span></h1>
        <div class="legenda-mini">
          <span class="tile demo correto">T</span>
          <span class="tile demo presente">E</span>
          <span class="tile demo ausente">X</span>
        </div>
      </div>

      <div class="inicio-tres-modos">
        <article
          class="modo-card modo-card-principal modo-diaria"
          :class="{ 'diaria-feita': store.diariaFeita }"
        >
          <span class="modo-badge">{{ store.diariaBadge }}</span>
          <h2>Palavra do dia</h2>
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
    </div>
  </section>
</template>
