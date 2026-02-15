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
  mode_acces: string | null
  mode_acces_label: string | null
}

import { computed } from 'vue'

const props = defineProps<{
  fonds: FundMatch[]
  selectedCode: string | null
}>()

const filteredFonds = computed(() => {
  if (!props.selectedCode) return props.fonds
  return props.fonds.filter(
    (f) => f.referentiel_code === props.selectedCode || !f.referentiel_code,
  )
})

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

function compatBadgeBg(pct: number): string {
  if (pct >= 75) return 'bg-emerald-50'
  if (pct >= 50) return 'bg-teal-50'
  if (pct >= 30) return 'bg-amber-50'
  return 'bg-red-50'
}

function modeAccesBadge(mode: string | null): { bg: string; text: string; label: string } {
  const map: Record<string, { bg: string; text: string; label: string }> = {
    banque_partenaire: { bg: 'bg-blue-50', text: 'text-blue-700', label: 'Via banque' },
    entite_accreditee: { bg: 'bg-violet-50', text: 'text-violet-700', label: 'Via entité accréditée' },
    appel_propositions: { bg: 'bg-orange-50', text: 'text-orange-700', label: 'Appel à propositions' },
    banque_multilaterale: { bg: 'bg-indigo-50', text: 'text-indigo-700', label: 'Via BMD' },
    direct: { bg: 'bg-emerald-50', text: 'text-emerald-700', label: 'Candidature directe' },
    garantie_bancaire: { bg: 'bg-cyan-50', text: 'text-cyan-700', label: 'Via votre banque' },
  }
  return map[mode ?? ''] ?? { bg: 'bg-gray-50', text: 'text-gray-600', label: 'Non spécifié' }
}
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
    <div class="mb-5 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50">
        <svg class="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-semibold text-gray-900">Fonds Verts Recommandés</h3>
        <p class="text-xs text-gray-500">Financements compatibles avec votre profil</p>
      </div>
    </div>

    <div v-if="filteredFonds.length === 0" class="rounded-xl bg-gray-50 py-8 text-center text-sm text-gray-400">
      Aucun fonds disponible
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="f in filteredFonds"
        :key="f.id"
        class="flex items-center gap-4 rounded-xl border border-gray-100 p-3 transition-colors hover:bg-gray-50"
      >
        <!-- Info -->
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-semibold text-gray-900">{{ f.nom }}</p>
          <div class="mt-1 flex flex-wrap items-center gap-2">
            <span v-if="f.institution" class="text-xs text-gray-500">{{ f.institution }}</span>
            <span v-if="f.referentiel_nom" class="rounded-md bg-gray-100 px-1.5 py-0.5 text-[11px] font-medium text-gray-600">
              {{ f.referentiel_nom }}
            </span>
            <span
              v-if="f.mode_acces"
              class="rounded-md px-1.5 py-0.5 text-[11px] font-medium"
              :class="[modeAccesBadge(f.mode_acces).bg, modeAccesBadge(f.mode_acces).text]"
            >
              {{ modeAccesBadge(f.mode_acces).label }}
            </span>
            <span v-if="f.montant_range" class="text-xs text-gray-400">{{ f.montant_range }}</span>
          </div>
          <p v-if="f.score_esg_minimum" class="mt-1 text-xs text-gray-400">
            Score ESG min : {{ f.score_esg_minimum }}/100
          </p>
        </div>

        <!-- Compatibilité -->
        <div class="flex shrink-0 flex-col items-center gap-1">
          <div class="rounded-lg px-2.5 py-1" :class="compatBadgeBg(f.compatibilite)">
            <span class="text-lg font-bold" :class="compatColor(f.compatibilite)">
              {{ f.compatibilite }}%
            </span>
          </div>
          <div class="h-1 w-12 overflow-hidden rounded-full bg-gray-100">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="compatBg(f.compatibilite)"
              :style="{ width: f.compatibilite + '%' }"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
