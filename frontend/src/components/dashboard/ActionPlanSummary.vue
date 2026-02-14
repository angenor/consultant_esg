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

function statusClass(s: string): string {
  if (s === 'en_cours') return 'border-blue-400 bg-blue-50'
  if (s === 'fait') return 'border-emerald-500 bg-emerald-500'
  return 'border-gray-300'
}
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
    <div class="mb-5 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50">
          <svg class="h-5 w-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
          </svg>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-gray-900">Plan d'Action</h3>
          <p v-if="plan" class="text-xs text-gray-500">{{ plan.titre }}</p>
        </div>
      </div>
      <button
        v-if="plan"
        class="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-emerald-600 transition-colors hover:bg-emerald-50"
        @click="router.push('/action-plan')"
      >
        Voir tout
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      </button>
    </div>

    <div v-if="!plan" class="rounded-xl bg-gray-50 py-8 text-center text-sm text-gray-400">
      Aucun plan d'action
    </div>

    <template v-else>
      <!-- Progress -->
      <div class="rounded-xl bg-gray-50 p-3">
        <div class="flex items-center justify-between text-xs text-gray-500">
          <span><span class="font-semibold text-gray-700">{{ plan.nb_fait }}</span> / {{ plan.nb_total }} actions</span>
          <span class="font-bold text-emerald-600">{{ plan.pourcentage }}%</span>
        </div>
        <div class="mt-2 h-2 overflow-hidden rounded-full bg-gray-200">
          <div
            class="h-full rounded-full bg-emerald-500 transition-all duration-700"
            :style="{ width: plan.pourcentage + '%' }"
          />
        </div>
      </div>

      <!-- Prochaines actions -->
      <div v-if="plan.prochaines_actions.length > 0" class="mt-4 space-y-2">
        <p class="text-xs font-semibold text-gray-500">Prochaines actions</p>
        <div
          v-for="a in plan.prochaines_actions"
          :key="a.id"
          class="flex items-start gap-2.5 rounded-lg p-2 transition-colors hover:bg-gray-50"
        >
          <div
            class="mt-0.5 h-4 w-4 shrink-0 rounded border-2"
            :class="statusClass(a.statut)"
          >
            <svg v-if="a.statut === 'fait'" class="h-full w-full text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-gray-800">{{ a.titre }}</p>
            <div class="mt-1 flex items-center gap-1.5">
              <span class="rounded-md px-1.5 py-0.5 text-[10px] font-semibold" :class="prioriteBadge(a.priorite)">
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
