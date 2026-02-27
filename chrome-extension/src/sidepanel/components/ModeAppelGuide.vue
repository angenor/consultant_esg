<template>
  <div class="px-4 py-3 bg-purple-50 border-b border-purple-100">
    <div class="flex items-center gap-2 mb-2">
      <span class="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full font-medium">
        Appel à propositions
      </span>
    </div>

    <!-- Alerte calendrier -->
    <div v-if="!calendarChecked"
         class="bg-amber-50 border border-amber-200 rounded-lg p-2 mb-2">
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-amber-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-xs text-amber-700">
          Vérifiez que l'appel à propositions est actuellement ouvert avant de commencer.
        </p>
      </div>
    </div>

    <!-- Étapes spécifiques -->
    <div class="space-y-2">
      <!-- Vérification calendrier -->
      <div class="flex items-start gap-2 p-2 rounded-lg"
           :class="calendarChecked ? 'bg-emerald-50' : 'bg-white'">
        <button @click="$emit('toggle-calendar')"
                class="w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors"
                :class="calendarChecked
                  ? 'bg-emerald-500 border-emerald-500'
                  : 'border-gray-300 hover:border-purple-400'">
          <svg v-if="calendarChecked" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </button>
        <div>
          <p class="text-xs font-medium" :class="calendarChecked ? 'text-emerald-700' : 'text-gray-700'">
            Calendrier vérifié
          </p>
          <p class="text-[11px] text-gray-500">L'appel est ouvert et la date limite n'est pas dépassée</p>
        </div>
      </div>

      <!-- Préparation note conceptuelle -->
      <div class="flex items-start gap-2 p-2 rounded-lg"
           :class="conceptNoteReady ? 'bg-emerald-50' : 'bg-white'">
        <button @click="$emit('toggle-concept-note')"
                class="w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors"
                :class="conceptNoteReady
                  ? 'bg-emerald-500 border-emerald-500'
                  : 'border-gray-300 hover:border-purple-400'">
          <svg v-if="conceptNoteReady" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </button>
        <div>
          <p class="text-xs font-medium" :class="conceptNoteReady ? 'text-emerald-700' : 'text-gray-700'">
            Note conceptuelle prête
          </p>
          <p class="text-[11px] text-gray-500">Le format demandé est respecté</p>
        </div>
      </div>
    </div>

    <!-- Délai si disponible -->
    <div v-if="delai" class="mt-2 text-[10px] text-purple-600">
      <span class="font-medium">Délai estimé :</span> {{ delai }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  calendarChecked: boolean
  conceptNoteReady: boolean
  delai?: string | null
}>()

defineEmits<{
  'toggle-calendar': []
  'toggle-concept-note': []
}>()
</script>
