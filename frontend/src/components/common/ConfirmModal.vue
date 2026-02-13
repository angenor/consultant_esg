<script setup lang="ts">
defineProps<{
  title?: string
  message?: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'warning'
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
        @click.self="emit('cancel')"
      >
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="scale-95 opacity-0"
          enter-to-class="scale-100 opacity-100"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="scale-100 opacity-100"
          leave-to-class="scale-95 opacity-0"
          appear
        >
          <div class="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <!-- Icon -->
            <div
              class="mx-auto flex h-12 w-12 items-center justify-center rounded-full"
              :class="variant === 'warning' ? 'bg-amber-100' : 'bg-red-100'"
            >
              <svg
                class="h-6 w-6"
                :class="variant === 'warning' ? 'text-amber-600' : 'text-red-600'"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>

            <!-- Text -->
            <h3 class="mt-4 text-center text-lg font-semibold text-gray-900">
              {{ title || 'Confirmer' }}
            </h3>
            <p class="mt-2 text-center text-sm text-gray-500">
              {{ message || 'Êtes-vous sûr de vouloir continuer ?' }}
            </p>

            <!-- Actions -->
            <div class="mt-6 flex gap-3">
              <button
                class="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                @click="emit('cancel')"
              >
                {{ cancelLabel || 'Annuler' }}
              </button>
              <button
                class="flex-1 rounded-lg px-4 py-2.5 text-sm font-medium text-white transition-colors"
                :class="variant === 'warning'
                  ? 'bg-amber-600 hover:bg-amber-700'
                  : 'bg-red-600 hover:bg-red-700'"
                @click="emit('confirm')"
              >
                {{ confirmLabel || 'Confirmer' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
