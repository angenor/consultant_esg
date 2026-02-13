<script setup lang="ts">
export interface FundMatch {
  id: string
  nom: string
  institution: string | null
  type: string | null
  referentiel_nom: string | null
  referentiel_code: string | null
  montant_range: string | null
  devise: string
  score_esg_minimum: number | null
  compatibilite: number
  date_limite: string | null
}

defineProps<{
  fonds: FundMatch[]
}>()

function compatColor(pct: number): string {
  if (pct >= 75) return 'text-emerald-600'
  if (pct >= 50) return 'text-teal-600'
  if (pct >= 30) return 'text-amber-600'
  return 'text-red-500'
}

function compatBg(pct: number): string {
  if (pct >= 75) return 'bg-emerald-500'
  if (pct >= 50) return 'bg-teal-500'
  if (pct >= 30) return 'bg-amber-500'
  return 'bg-red-500'
}
</script>

<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
    <h3 class="text-sm font-semibold text-gray-700">Fonds Verts Recommandés</h3>

    <div v-if="fonds.length === 0" class="mt-4 text-center text-sm text-gray-400">
      Aucun fonds disponible
    </div>

    <div v-else class="mt-4 divide-y divide-gray-100">
      <div
        v-for="f in fonds"
        :key="f.id"
        class="flex items-center gap-4 py-3 first:pt-0 last:pb-0"
      >
        <!-- Info -->
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-semibold text-gray-800">{{ f.nom }}</p>
          <div class="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            <span v-if="f.institution">{{ f.institution }}</span>
            <span v-if="f.referentiel_nom" class="rounded bg-gray-100 px-1.5 py-0.5 text-gray-600">
              {{ f.referentiel_nom }}
            </span>
            <span v-if="f.montant_range">{{ f.montant_range }}</span>
          </div>
          <p v-if="f.score_esg_minimum" class="mt-0.5 text-xs text-gray-400">
            Score ESG min : {{ f.score_esg_minimum }}/100
          </p>
        </div>

        <!-- Compatibilité -->
        <div class="flex flex-col items-center">
          <span class="text-lg font-bold" :class="compatColor(f.compatibilite)">
            {{ f.compatibilite }}%
          </span>
          <div class="mt-1 h-1 w-12 overflow-hidden rounded-full bg-gray-100">
            <div
              class="h-full rounded-full"
              :class="compatBg(f.compatibilite)"
              :style="{ width: f.compatibilite + '%' }"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
