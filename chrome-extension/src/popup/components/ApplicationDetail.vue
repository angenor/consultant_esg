<template>
  <div class="p-4">
    <!-- Header avec retour -->
    <button @click="$emit('back')" class="flex items-center gap-1 text-sm text-gray-500 mb-3">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      {{ t('back') }}
    </button>

    <!-- Info fonds -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-4">
      <h2 class="font-semibold text-gray-800">{{ application.fonds_nom }}</h2>
      <p class="text-sm text-gray-500">{{ application.fonds_institution }}</p>

      <!-- Progression -->
      <div class="mt-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-gray-600">{{ t('progression') }}</span>
          <span class="text-xs font-bold text-emerald-600">{{ application.progress_pct }}%</span>
        </div>
        <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div class="h-full bg-emerald-500 rounded-full transition-all"
               :style="{ width: application.progress_pct + '%' }"></div>
        </div>
      </div>

      <!-- Statut -->
      <div class="mt-3 flex items-center gap-2">
        <span class="text-xs px-2 py-1 rounded-full font-medium"
              :class="statusClasses">
          {{ statusLabel }}
        </span>
        <span class="text-xs text-gray-400">
          {{ t('started_on', formatDate(application.started_at)) }}
        </span>
      </div>
    </div>

    <!-- Etapes completes -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-4">
      <h3 class="text-sm font-semibold text-gray-800 mb-3">{{ t('steps') }}</h3>
      <div class="space-y-2">
        <div v-for="step in steps" :key="step.order"
             class="flex items-center gap-2">
          <div class="w-5 h-5 rounded-full flex items-center justify-center"
               :class="step.order <= application.current_step
                 ? 'bg-emerald-500'
                 : step.order === application.current_step + 1
                   ? 'bg-blue-500'
                   : 'bg-gray-200'">
            <svg v-if="step.order <= application.current_step"
                 class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
            <span v-else class="text-[10px] font-bold"
                  :class="step.order === application.current_step + 1 ? 'text-white' : 'text-gray-500'">
              {{ step.order }}
            </span>
          </div>
          <span class="text-sm" :class="step.order <= application.current_step
            ? 'text-gray-800' : 'text-gray-400'">
            {{ step.title }}
          </span>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="space-y-2">
      <button
        v-if="application.url_candidature"
        @click="openAndGuide"
        class="w-full bg-emerald-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium
               hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {{ t('resume_application') }}
      </button>

      <button
        v-if="application.status === 'en_cours'"
        @click="markAsSubmitted"
        class="w-full border border-emerald-300 text-emerald-700 rounded-lg px-4 py-2 text-sm
               font-medium hover:bg-emerald-50 transition-colors"
      >
        {{ t('mark_submitted') }}
      </button>

      <button
        @click="abandonApplication"
        class="w-full text-red-500 text-xs hover:text-red-600"
      >
        {{ t('abandon') }}
      </button>
    </div>

    <!-- Notes -->
    <div class="mt-4">
      <label class="text-xs font-medium text-gray-600">{{ t('personal_notes') }}</label>
      <textarea
        v-model="notes"
        @blur="saveNotes"
        rows="3"
        :placeholder="t('add_notes')"
        class="w-full mt-1 border border-gray-300 rounded-lg px-3 py-2 text-sm
               outline-none focus:border-emerald-500 resize-none"
      ></textarea>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FundApplication, FundStep } from '@shared/types'
import { APPLICATION_STATUSES } from '@shared/constants'
import { useApplications } from '@shared/stores/applications'
import { t } from '@shared/i18n'

const props = defineProps<{
  application: FundApplication
  steps: FundStep[]
}>()

const emit = defineEmits<{
  back: []
  updated: []
}>()

const { updateApplication } = useApplications()
const notes = ref(props.application.notes || '')

const statusConfig = computed(() => APPLICATION_STATUSES[props.application.status])
const statusLabel = computed(() => statusConfig.value?.label || props.application.status)
const statusClasses = computed(() => {
  const color = statusConfig.value?.color || 'gray'
  return `bg-${color}-100 text-${color}-700`
})

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR')
}

async function openAndGuide() {
  if (props.application.url_candidature) {
    await chrome.tabs.create({ url: props.application.url_candidature })
  }
}

async function markAsSubmitted() {
  await updateApplication(props.application.id, {
    status: 'soumise',
    submitted_at: new Date().toISOString(),
  })
  emit('updated')
}

async function abandonApplication() {
  await updateApplication(props.application.id, { status: 'abandonnee' })
  emit('updated')
}

async function saveNotes() {
  await updateApplication(props.application.id, { notes: notes.value })
}
</script>
