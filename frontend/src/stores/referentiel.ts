import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export interface ReferentielOption {
  id: string
  nom: string
  code: string
  institution: string | null
}

export const useReferentielStore = defineStore('referentiel', () => {
  // --------------- State ---------------
  const referentiels = ref<ReferentielOption[]>([])
  const selectedCode = ref<string | null>(
    localStorage.getItem('selectedReferentielCode'),
  )

  // --------------- Getters ---------------
  const selectedReferentiel = computed(() =>
    referentiels.value.find((r) => r.code === selectedCode.value) || null,
  )

  // --------------- Actions ---------------
  function setReferentiels(list: ReferentielOption[]) {
    referentiels.value = list
    // Si le code stocké n'existe plus dans la liste, reset au premier
    if (selectedCode.value && !list.find((r) => r.code === selectedCode.value)) {
      select(list[0]?.code ?? null)
    }
  }

  function select(code: string | null) {
    selectedCode.value = code
    if (code) {
      localStorage.setItem('selectedReferentielCode', code)
    } else {
      localStorage.removeItem('selectedReferentielCode')
    }
  }

  return {
    referentiels,
    selectedCode,
    selectedReferentiel,
    setReferentiels,
    select,
  }
})
