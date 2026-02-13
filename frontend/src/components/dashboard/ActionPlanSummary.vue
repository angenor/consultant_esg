<script setup lang="ts">
import { useRouter } from 'vue-router'

export interface ActionSummary {
  id: string
  titre: string
  nb_total: number
  nb_fait: number
  pourcentage: number
  prochaines_actions: {
    id: string
    titre: string
    pilier: string | null
    priorite: string
    statut: string
    echeance: string | null
  }[]
}

const props = defineProps<{
  plan: ActionSummary | null
}>()

const router = useRouter()

function prioriteLabel(p: string): string {
  if (p === 'quick_win') return 'Quick Win'
  if (p === 'moyen_terme') return 'Moyen terme'
  if (p === 'long_terme') return 'Long terme'
  return p
}

function prioriteBadge(p: string): string {
  if (p === 'quick_win') return 'bg-emerald-100 text-emerald-700'
  if (p === 'moyen_terme') return 'bg-blue-100 text-blue-700'
  return 'bg-purple-100 text-purple-700'
}
</script>

<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-gray-700">Plan d'Action</h3>
      <button
        v-if="plan"
        class="text-xs font-medium text-emerald-600 hover:text-emerald-700"
        @click="router.push('/action-plan')"
      >
        Voir tout
      </button>
    </div>

    <div v-if="!plan" class="mt-4 text-center text-sm text-gray-400">
      Aucun plan d'action
    </div>

    <template v-else>
      <!-- Progress -->
      <div class="mt-3">
        <div class="flex items-center justify-between text-xs text-gray-500">
          <span>{{ plan.nb_fait }}/{{ plan.nb_total }} actions</span>
          <span class="font-semibold text-emerald-600">{{ plan.pourcentage }}%</span>
        </div>
        <div class="mt-1 h-2 overflow-hidden rounded-full bg-gray-100">
          <div
            class="h-full rounded-full bg-emerald-500 transition-all duration-500"
            :style="{ width: plan.pourcentage + '%' }"
          />
        </div>
      </div>

      <!-- Prochaines actions -->
      <div v-if="plan.prochaines_actions.length > 0" class="mt-4 space-y-2">
        <p class="text-xs font-medium text-gray-500">Prochaines actions :</p>
        <div
          v-for="a in plan.prochaines_actions"
          :key="a.id"
          class="flex items-start gap-2 text-sm"
        >
          <div
            class="mt-1 h-3 w-3 flex-shrink-0 rounded-full border-2"
            :class="a.statut === 'en_cours' ? 'border-amber-400 bg-amber-100' : 'border-gray-300'"
          />
          <div class="min-w-0 flex-1">
            <p class="truncate text-gray-700">{{ a.titre }}</p>
            <div class="mt-0.5 flex items-center gap-1">
              <span class="rounded px-1.5 py-0.5 text-[10px] font-medium" :class="prioriteBadge(a.priorite)">
                {{ prioriteLabel(a.priorite) }}
              </span>
              <span v-if="a.echeance" class="text-[10px] text-gray-400">
                {{ new Date(a.echeance).toLocaleDateString('fr-FR') }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
