<script setup lang="ts">
export interface ActionItemData {
  id: string
  titre: string
  description?: string
  priorite: string
  pilier?: string
  statut: string
  echeance?: string | null
  impact_score_estime?: number
}

const props = defineProps<{
  item: ActionItemData
}>()

const emit = defineEmits<{
  toggleStatus: [id: string, newStatus: string]
}>()

function nextStatus(current: string): string {
  if (current === 'a_faire') return 'en_cours'
  if (current === 'en_cours') return 'fait'
  return 'a_faire'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { a_faire: 'A faire', en_cours: 'En cours', fait: 'Fait' }
  return map[s] || s
}

function statusClass(s: string): string {
  const map: Record<string, string> = {
    a_faire: 'bg-gray-100 text-gray-600',
    en_cours: 'bg-blue-100 text-blue-700',
    fait: 'bg-emerald-100 text-emerald-700',
  }
  return map[s] || 'bg-gray-100 text-gray-600'
}

function pilierLabel(p: string | undefined): string {
  const map: Record<string, string> = { E: 'Environnement', S: 'Social', G: 'Gouvernance' }
  return map[p || ''] || ''
}

function pilierClass(p: string | undefined): string {
  const map: Record<string, string> = {
    E: 'bg-green-100 text-green-700',
    S: 'bg-purple-100 text-purple-700',
    G: 'bg-indigo-100 text-indigo-700',
  }
  return map[p || ''] || 'bg-gray-100 text-gray-600'
}

function formatDate(d: string | null | undefined): string {
  if (!d) return ''
  try {
    return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return d
  }
}

function isOverdue(d: string | null | undefined, statut: string): boolean {
  if (!d || statut === 'fait') return false
  return new Date(d) < new Date()
}
</script>

<template>
  <div
    class="group rounded-xl border bg-white p-4 shadow-sm transition-all hover:shadow-md"
    :class="[
      item.statut === 'fait' ? 'border-emerald-200 bg-emerald-50/30' : 'border-gray-200',
    ]"
  >
    <div class="flex items-start gap-3">
      <!-- Toggle button -->
      <button
        class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border-2 transition-all"
        :class="
          item.statut === 'fait'
            ? 'border-emerald-500 bg-emerald-500 text-white hover:border-red-400 hover:bg-red-400'
            : item.statut === 'en_cours'
              ? 'border-blue-400 bg-blue-50 hover:border-blue-500'
              : 'border-gray-300 hover:border-emerald-400 hover:bg-emerald-50'
        "
        :title="`Passer a : ${statusLabel(nextStatus(item.statut))}`"
        @click="emit('toggleStatus', item.id, nextStatus(item.statut))"
      >
        <svg v-if="item.statut === 'fait'" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        <span v-else-if="item.statut === 'en_cours'" class="h-2 w-2 rounded-full bg-blue-500" />
      </button>

      <!-- Content -->
      <div class="min-w-0 flex-1">
        <p
          class="text-sm font-semibold"
          :class="item.statut === 'fait' ? 'text-gray-400 line-through' : 'text-gray-900'"
        >
          {{ item.titre }}
        </p>
        <p v-if="item.description" class="mt-1 text-xs leading-relaxed text-gray-500 line-clamp-2">
          {{ item.description }}
        </p>

        <!-- Tags -->
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <span class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold" :class="statusClass(item.statut)">
            {{ statusLabel(item.statut) }}
          </span>
          <span v-if="item.pilier" class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold" :class="pilierClass(item.pilier)">
            {{ pilierLabel(item.pilier) }}
          </span>
          <span
            v-if="item.echeance"
            class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium"
            :class="isOverdue(item.echeance, item.statut) ? 'bg-red-100 font-semibold text-red-600' : 'bg-gray-100 text-gray-500'"
          >
            <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
            {{ formatDate(item.echeance) }}
          </span>
        </div>
      </div>

      <!-- Impact -->
      <div v-if="item.impact_score_estime" class="shrink-0 text-right">
        <div class="rounded-lg bg-emerald-50 px-2.5 py-1.5">
          <span class="text-sm font-bold text-emerald-600">+{{ item.impact_score_estime }}</span>
          <p class="text-[10px] font-medium text-emerald-500">pts ESG</p>
        </div>
      </div>
    </div>
  </div>
</template>
