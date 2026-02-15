<template>
  <div class="p-4 space-y-4">
    <!-- Carte Entreprise -->
    <div v-if="data?.entreprise" class="bg-white rounded-xl border border-gray-200 p-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
          <span class="text-emerald-700 font-bold text-sm">
            {{ data.entreprise.nom.substring(0, 2).toUpperCase() }}
          </span>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-gray-800 text-sm truncate">
            {{ data.entreprise.nom }}
          </h3>
          <p class="text-xs text-gray-500">
            {{ data.entreprise.secteur || 'Secteur non defini' }} · {{ data.entreprise.pays }}
          </p>
        </div>
        <div v-if="latestScore" class="text-right">
          <div class="text-lg font-bold" :class="scoreColor">
            {{ latestScore.score_global }}/100
          </div>
          <div class="text-xs text-gray-500">{{ t('esg_score') }}</div>
        </div>
      </div>
    </div>

    <!-- Pas d'entreprise -->
    <div v-else class="bg-amber-50 rounded-xl border border-amber-200 p-4 text-center">
      <p class="text-sm text-amber-700">{{ t('no_company') }}</p>
      <a href="http://localhost:5173/dashboard" target="_blank"
         class="text-xs text-amber-600 hover:underline mt-1 inline-block">
        {{ t('configure_company') }}
      </a>
    </div>

    <!-- Candidatures en cours -->
    <section>
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-800 text-sm">{{ t('applications_title') }}</h3>
        <span class="text-xs text-gray-400">{{ activeApplications.length }}</span>
      </div>

      <div v-if="activeApplications.length === 0"
           class="bg-white rounded-xl border border-dashed border-gray-300 p-4 text-center">
        <p class="text-sm text-gray-500">{{ t('no_applications') }}</p>
        <p class="text-xs text-gray-400 mt-1">
          {{ t('no_applications_hint') }}
        </p>
      </div>

      <div v-else class="space-y-2">
        <ApplicationCard
          v-for="app in activeApplications"
          :key="app.id"
          :application="app"
          @click="$emit('select-application', app)"
        />
      </div>
    </section>

    <!-- Fonds recommandes -->
    <section v-if="data?.fonds_recommandes?.length">
      <h3 class="font-semibold text-gray-800 text-sm mb-2">{{ t('funds_recommended') }}</h3>
      <div class="space-y-2">
        <FundRecommendation
          v-for="fonds in data.fonds_recommandes.slice(0, 3)"
          :key="fonds.id"
          :fonds="fonds"
        />
      </div>
    </section>

    <!-- Derniere synchro -->
    <div class="flex items-center justify-between text-xs text-gray-400 pt-2">
      <span v-if="data?.last_synced">
        Maj : {{ formatRelativeTime(data.last_synced) }}
      </span>
      <button
        @click="$emit('refresh')"
        :disabled="loading"
        class="text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
      >
        <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }"
             fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11
                11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {{ t('sync_refresh') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SyncedData, ESGScore, FundApplication } from '@shared/types'
import { t } from '@shared/i18n'
import ApplicationCard from './ApplicationCard.vue'
import FundRecommendation from './FundRecommendation.vue'

const props = defineProps<{
  data: SyncedData | null
  loading: boolean
}>()

defineEmits<{
  refresh: []
  'select-application': [app: FundApplication]
}>()

const latestScore = computed<ESGScore | null>(() => {
  if (!props.data?.scores?.length) return null
  return props.data.scores.reduce((latest, score) =>
    new Date(score.created_at) > new Date(latest.created_at) ? score : latest
  )
})

const scoreColor = computed(() => {
  const score = latestScore.value?.score_global
  if (!score) return 'text-gray-400'
  if (score >= 70) return 'text-emerald-600'
  if (score >= 40) return 'text-amber-600'
  return 'text-red-600'
})

const activeApplications = computed(() => {
  if (!props.data?.applications) return []
  return props.data.applications.filter(
    app => ['brouillon', 'en_cours'].includes(app.status)
  )
})

function formatRelativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return "a l'instant"
  if (minutes < 60) return `il y a ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `il y a ${hours}h`
  const days = Math.floor(hours / 24)
  return `il y a ${days}j`
}
</script>
