<script setup>
import { computed } from "vue";
import { MetaAvatar } from "../../utils/avatares.js";

const props = defineProps({
  avatarId: { type: String, required: true },
});

const meta = computed(() => MetaAvatar(props.avatarId));
const traco = "#1a1520";
const pele = "#f5e6c8";
</script>

<template>
  <svg
    class="avatar-ilustracao"
    viewBox="0 0 48 48"
    role="img"
    :aria-label="`Avatar ${meta.nome}`"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="24" cy="24" r="23" :fill="meta.corFundo" />
    <circle cx="24" cy="24" r="22" fill="none" :stroke="traco" stroke-width="1.5" opacity="0.25" />

    <!-- folha -->
    <g v-if="avatarId === 'folha'">
      <ellipse cx="24" cy="26" rx="11" ry="10" :fill="pele" :stroke="traco" stroke-width="2.2" />
      <circle cx="19" cy="24" r="2" :fill="traco" />
      <circle cx="29" cy="24" r="2" :fill="traco" />
      <path d="M20 30 Q24 33 28 30" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
      <path d="M24 14 Q18 20 24 22 Q30 20 24 14" fill="#5fad62" :stroke="traco" stroke-width="2" />
    </g>

    <!-- broto -->
    <g v-else-if="avatarId === 'broto'">
      <ellipse cx="24" cy="27" rx="10" ry="9" :fill="pele" :stroke="traco" stroke-width="2.2" />
      <circle cx="20" cy="25" r="1.8" :fill="traco" />
      <circle cx="28" cy="25" r="1.8" :fill="traco" />
      <path d="M21 30 Q24 32 27 30" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
      <path d="M24 12 L24 18 M20 16 L24 12 L28 16" fill="none" :stroke="traco" stroke-width="2.2" stroke-linecap="round" />
      <ellipse cx="24" cy="10" rx="4" ry="3" fill="#8ed99a" :stroke="traco" stroke-width="1.8" />
    </g>

    <!-- sol -->
    <g v-else-if="avatarId === 'sol'">
      <circle cx="24" cy="26" r="10" :fill="pele" :stroke="traco" stroke-width="2.2" />
      <circle cx="20" cy="24" r="2" :fill="traco" />
      <circle cx="28" cy="24" r="2" :fill="traco" />
      <path d="M20 30 Q24 33 28 30" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
      <circle cx="24" cy="14" r="7" fill="#ffe08a" :stroke="traco" stroke-width="2" />
      <g :stroke="traco" stroke-width="2" stroke-linecap="round">
        <line x1="24" y1="4" x2="24" y2="7" />
        <line x1="24" y1="21" x2="24" y2="24" />
        <line x1="14" y1="8" x2="16" y2="10" />
        <line x1="32" y1="8" x2="30" y2="10" />
        <line x1="10" y1="14" x2="12" y2="15" />
        <line x1="36" y1="14" x2="34" y2="15" />
      </g>
    </g>

    <!-- nuvem -->
    <g v-else-if="avatarId === 'nuvem'">
      <ellipse cx="24" cy="27" rx="10" ry="9" :fill="pele" :stroke="traco" stroke-width="2.2" />
      <circle cx="20" cy="25" r="1.8" :fill="traco" />
      <circle cx="28" cy="25" r="1.8" :fill="traco" />
      <path d="M21 30 Q24 32 27 30" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
      <path d="M14 18 Q18 12 24 14 Q30 12 34 18 Q36 22 32 24 Q28 26 24 24 Q18 26 14 22 Z" fill="#e8f0f8" :stroke="traco" stroke-width="2" />
    </g>

    <!-- cogumelo -->
    <g v-else-if="avatarId === 'cogumelo'">
      <ellipse cx="24" cy="28" rx="9" ry="8" :fill="pele" :stroke="traco" stroke-width="2.2" />
      <circle cx="21" cy="26" r="1.6" :fill="traco" />
      <circle cx="27" cy="26" r="1.6" :fill="traco" />
      <path d="M22 30 Q24 31 26 30" fill="none" :stroke="traco" stroke-width="1.8" stroke-linecap="round" />
      <path d="M14 20 Q24 10 34 20 Q32 24 24 22 Q16 24 14 20 Z" fill="#e8d0c8" :stroke="traco" stroke-width="2" />
      <circle cx="20" cy="17" r="2.5" fill="#fff" opacity="0.7" />
      <circle cx="28" cy="18" r="2" fill="#fff" opacity="0.6" />
      <rect x="21" y="22" width="6" height="6" rx="1" fill="#f0e0d0" :stroke="traco" stroke-width="1.5" />
    </g>

    <!-- coruja -->
    <g v-else-if="avatarId === 'coruja'">
      <ellipse cx="24" cy="26" rx="12" ry="11" fill="#8a8498" :stroke="traco" stroke-width="2.2" />
      <circle cx="19" cy="24" r="4" fill="#fff" :stroke="traco" stroke-width="1.8" />
      <circle cx="29" cy="24" r="4" fill="#fff" :stroke="traco" stroke-width="1.8" />
      <circle cx="19" cy="24" r="2" :fill="traco" />
      <circle cx="29" cy="24" r="2" :fill="traco" />
      <path d="M24 28 L22 31 L26 31 Z" fill="#c9a227" :stroke="traco" stroke-width="1.5" />
      <path d="M18 16 L24 20 L30 16" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
    </g>

    <!-- raposa -->
    <g v-else-if="avatarId === 'raposa'">
      <ellipse cx="24" cy="27" rx="10" ry="9" fill="#e8a060" :stroke="traco" stroke-width="2.2" />
      <circle cx="20" cy="25" r="1.8" :fill="traco" />
      <circle cx="28" cy="25" r="1.8" :fill="traco" />
      <path d="M22 29 Q24 31 26 29" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
      <path d="M16 18 L20 26 M32 18 L28 26" fill="none" :stroke="traco" stroke-width="2.2" stroke-linecap="round" />
      <path d="M18 14 L24 20 L30 14" fill="#e8a060" :stroke="traco" stroke-width="2" />
      <circle cx="24" cy="18" r="3" fill="#fff" opacity="0.35" />
    </g>

    <!-- gato -->
    <g v-else-if="avatarId === 'gato'">
      <ellipse cx="24" cy="27" rx="10" ry="9" fill="#b0a8c0" :stroke="traco" stroke-width="2.2" />
      <ellipse cx="20" cy="25" rx="2" ry="2.5" :fill="traco" />
      <ellipse cx="28" cy="25" rx="2" ry="2.5" :fill="traco" />
      <path d="M22 30 L24 28 L26 30" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
      <path d="M16 16 L20 22 M32 16 L28 22" fill="none" :stroke="traco" stroke-width="2.2" stroke-linejoin="round" />
      <path d="M22 30 Q24 32 26 30" fill="none" :stroke="traco" stroke-width="1.5" />
    </g>

    <!-- peixe -->
    <g v-else-if="avatarId === 'peixe'">
      <ellipse cx="22" cy="26" rx="11" ry="9" fill="#7ec8e0" :stroke="traco" stroke-width="2.2" />
      <circle cx="19" cy="24" r="2" :fill="traco" />
      <circle cx="25" cy="24" r="2" :fill="traco" />
      <path d="M20 29 Q22 31 24 29" fill="none" :stroke="traco" stroke-width="1.8" stroke-linecap="round" />
      <path d="M34 26 L38 24 L38 28 Z" fill="#5ab0c8" :stroke="traco" stroke-width="2" />
      <path d="M12 22 Q10 26 12 30" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
    </g>

    <!-- abelha -->
    <g v-else-if="avatarId === 'abelha'">
      <ellipse cx="24" cy="26" rx="10" ry="9" fill="#ffe08a" :stroke="traco" stroke-width="2.2" />
      <circle cx="20" cy="24" r="1.8" :fill="traco" />
      <circle cx="28" cy="24" r="1.8" :fill="traco" />
      <path d="M21 29 Q24 31 27 29" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
      <path d="M18 20 L30 20 M18 24 L30 24 M18 28 L30 28" :stroke="traco" stroke-width="2.5" opacity="0.35" />
      <path d="M16 14 L20 18 M28 18 L32 14" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
      <ellipse cx="24" cy="12" rx="5" ry="3" fill="#fff" opacity="0.5" :stroke="traco" stroke-width="1.5" />
    </g>

    <!-- tulipa -->
    <g v-else-if="avatarId === 'tulipa'">
      <ellipse cx="24" cy="28" rx="9" ry="8" :fill="pele" :stroke="traco" stroke-width="2.2" />
      <circle cx="21" cy="26" r="1.6" :fill="traco" />
      <circle cx="27" cy="26" r="1.6" :fill="traco" />
      <path d="M22 30 Q24 31 26 30" fill="none" :stroke="traco" stroke-width="1.8" stroke-linecap="round" />
      <path d="M18 18 Q24 8 30 18 Q28 22 24 20 Q20 22 18 18 Z" fill="#e87898" :stroke="traco" stroke-width="2" />
      <path d="M24 20 L24 36" fill="none" :stroke="traco" stroke-width="2.2" stroke-linecap="round" />
      <path d="M20 34 Q24 38 28 34" fill="none" :stroke="traco" stroke-width="2" stroke-linecap="round" />
    </g>

    <!-- pinheiro -->
    <g v-else-if="avatarId === 'pinheiro'">
      <ellipse cx="24" cy="28" rx="9" ry="8" :fill="pele" :stroke="traco" stroke-width="2.2" />
      <circle cx="21" cy="26" r="1.6" :fill="traco" />
      <circle cx="27" cy="26" r="1.6" :fill="traco" />
      <path d="M22 30 Q24 31 26 30" fill="none" :stroke="traco" stroke-width="1.8" stroke-linecap="round" />
      <path d="M24 10 L16 22 L24 18 L32 22 Z" fill="#3d7a4a" :stroke="traco" stroke-width="2" />
      <path d="M24 18 L14 30 L24 26 L34 30 Z" fill="#5fad62" :stroke="traco" stroke-width="2" />
      <rect x="22" y="30" width="4" height="6" rx="1" fill="#6b4a32" :stroke="traco" stroke-width="1.5" />
    </g>

    <!-- fallback folha -->
    <g v-else>
      <ellipse cx="24" cy="26" rx="11" ry="10" :fill="pele" :stroke="traco" stroke-width="2.2" />
      <circle cx="19" cy="24" r="2" :fill="traco" />
      <circle cx="29" cy="24" r="2" :fill="traco" />
      <path d="M24 14 Q18 20 24 22 Q30 20 24 14" fill="#5fad62" :stroke="traco" stroke-width="2" />
    </g>
  </svg>
</template>
