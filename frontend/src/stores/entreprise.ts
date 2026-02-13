import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useApi } from '../composables/useApi'

export interface Entreprise {
  id: string
  nom: string
  secteur: string | null
  sous_secteur: string | null
  pays: string
  ville: string | null
  effectifs: number | null
  chiffre_affaires: number | null
  devise: string
  description: string | null
  profil_json: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface CreateEntreprisePayload {
  nom: string
  secteur?: string
  pays?: string
  ville?: string
  effectifs?: number
  description?: string
}

export const useEntrepriseStore = defineStore('entreprise', () => {
  const { get, post } = useApi()

  // --------------- State ---------------
  const entreprises = ref<Entreprise[]>([])
  const activeEntrepriseId = ref<string | null>(null)
  const isLoading = ref(false)

  // --------------- Getters ---------------
  const activeEntreprise = computed(() =>
    entreprises.value.find((e) => e.id === activeEntrepriseId.value) || null,
  )

  // --------------- Actions ---------------
  async function loadEntreprises() {
    isLoading.value = true
    try {
      entreprises.value = await get<Entreprise[]>('/api/entreprises/')
      // Auto-select first if none selected
      const first = entreprises.value[0]
      if (!activeEntrepriseId.value && first) {
        activeEntrepriseId.value = first.id
      }
    } finally {
      isLoading.value = false
    }
  }

  async function createEntreprise(data: CreateEntreprisePayload): Promise<Entreprise> {
    const entreprise = await post<Entreprise>('/api/entreprises/', data)
    entreprises.value.unshift(entreprise)
    activeEntrepriseId.value = entreprise.id
    return entreprise
  }

  function selectEntreprise(id: string) {
    activeEntrepriseId.value = id
  }

  return {
    entreprises,
    activeEntrepriseId,
    activeEntreprise,
    isLoading,
    loadEntreprises,
    createEntreprise,
    selectEntreprise,
  }
})
