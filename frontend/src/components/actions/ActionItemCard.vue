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
  const map: Record<string, string> = { a_faire: 'À faire', en_cours: 'En cours', fait: 'Fait' }
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

function prioriteLabel(p: string): string {
  const map: Record<string, string> = { quick_win: 'Quick-win', moyen_terme: 'Moyen terme', long_terme: 'Long terme' }
  return map[p] || p
}

function prioriteClass(p: string): string {
  const map: Record<string, string> = {
    quick_win: 'border-emerald-200 bg-emerald-50',
    moyen_terme: 'border-blue-200 bg-blue-50',
    long_terme: 'border-amber-200 bg-amber-50',
  }
  return map[p] || 'border-gray-200 bg-gray-50'
}

function pilierIcon(p: string | undefined): string {
  const map: Record<string, string> = { E: '🌿', S: '👥', G: '🏛️' }
  return map[p || ''] || '📋'
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
    class="rounded-xl border p-4 shadow-sm transition-colors"
    :class="[prioriteClass(item.priorite), item.statut === 'fait' ? 'opacity-70' : '']"
  >
    <div class="flex items-start justify-between gap-3">
      <!-- Left: checkbox + content -->
      <div class="flex items-start gap-3">
        <!-- Toggle button -->
        <button
          v-if="item.statut !== 'fait'"
          class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 transition-colors"
          :class="item.statut === 'en_cours' ? 'border-blue-400 bg-blue-100' : 'border-gray-300 hover:border-emerald-400'"
          :title="`Passer à : ${statusLabel(nextStatus(item.statut))}`"
          @click="emit('toggleStatus', item.id, nextStatus(item.statut))"
        >
          <span v-if="item.statut === 'en_cours'" class="h-2 w-2 rounded-full bg-blue-500" />
        </button>
        <button
          v-else
          class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-emerald-500 text-white transition-colors hover:bg-red-400"
          :title="`Passer à : ${statusLabel(nextStatus(item.statut))}`"
          @click="emit('toggleStatus', item.id, nextStatus(item.statut))"
        >
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </button>

        <div>
          <p class="text-sm font-medium text-gray-800" :class="{ 'line-through': item.statut === 'fait' }">
            {{ pilierIcon(item.pilier) }} {{ item.titre }}
          </p>
          <p v-if="item.description" class="mt-0.5 text-xs text-gray-500 line-clamp-2">
            {{ item.description }}
          </p>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <span class="inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold" :class="statusClass(item.statut)">
              {{ statusLabel(item.statut) }}
            </span>
            <span class="text-[10px] font-medium text-gray-400">
              {{ prioriteLabel(item.priorite) }}
            </span>
            <span
              v-if="item.echeance"
              class="text-[10px]"
              :class="isOverdue(item.echeance, item.statut) ? 'font-semibold text-red-500' : 'text-gray-400'"
            >
              {{ isOverdue(item.echeance, item.statut) ? '⚠️ ' : '' }}{{ formatDate(item.echeance) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Right: impact -->
      <div v-if="item.impact_score_estime" class="shrink-0 text-right">
        <span class="text-sm font-semibold text-emerald-600">+{{ item.impact_score_estime }}</span>
        <p class="text-[10px] text-gray-400">pts ESG</p>
      </div>
    </div>
  </div>
</template>
