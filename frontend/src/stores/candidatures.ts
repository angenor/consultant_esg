import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useApi } from '../composables/useApi'

export interface Candidature {
  id: string
  fonds_id: string | null
  fonds_nom: string
  fonds_institution: string
  status: string
  progress_pct: number
  current_step: number
  total_steps: number | null
  url_candidature: string | null
  notes: string | null
  started_at: string
  submitted_at: string | null
  updated_at: string
  next_step: string | null
  dossier_id: string | null
  documents_count: number
}

export interface CandidatureDetail extends Candidature {
  form_data: Record<string, unknown> | null
  timeline: TimelineStep[]
  documents: CandidatureDocument[]
  history: HistoryEntry[]
}

export interface TimelineStep {
  title: string
  status: 'done' | 'current' | 'pending'
  date: string | null
  estimated: string | null
  description: string | null
  actions: { type: string; label: string }[]
}

export interface CandidatureDocument {
  nom: string
  type: string
  url_docx: string | null
  url_pdf: string | null
  date: string
}

export interface HistoryEntry {
  date: string
  action: string
  details?: string
}

export interface CandidatureStats {
  total: number
  brouillon: number
  en_cours: number
  soumise: number
  acceptee: number
  refusee: number
  abandonnee: number
}

export interface CandidatureFilters {
  status?: string
  fonds_id?: string
}

export const useCandidaturesStore = defineStore('candidatures', () => {
  const { get, post, put } = useApi()

  const candidatures = ref<Candidature[]>([])
  const currentDetail = ref<CandidatureDetail | null>(null)
  const stats = ref<CandidatureStats | null>(null)
  const loading = ref(false)
  const loadingDetail = ref(false)

  const activeCount = computed(() =>
    candidatures.value.filter((c) => ['brouillon', 'en_cours'].includes(c.status)).length,
  )

  const activeCandidatures = computed(() =>
    candidatures.value.filter((c) => ['brouillon', 'en_cours'].includes(c.status)),
  )

  async function loadCandidatures(filters?: CandidatureFilters) {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (filters?.status) params.set('status', filters.status)
      if (filters?.fonds_id) params.set('fonds_id', filters.fonds_id)
      const qs = params.toString()
      const url = `/api/candidatures/${qs ? '?' + qs : ''}`
      candidatures.value = (await get<Candidature[]>(url)) ?? []
    } catch {
      candidatures.value = []
    } finally {
      loading.value = false
    }
  }

  async function loadStats() {
    try {
      stats.value = await get<CandidatureStats>('/api/candidatures/stats')
    } catch {
      stats.value = null
    }
  }

  async function getCandidature(id: string) {
    loadingDetail.value = true
    try {
      currentDetail.value = await get<CandidatureDetail>(`/api/candidatures/${id}`)
    } catch {
      currentDetail.value = null
    } finally {
      loadingDetail.value = false
    }
  }

  async function createCandidature(data: {
    fonds_id?: string
    fonds_nom: string
    fonds_institution?: string
    notes?: string
  }) {
    const result = await post<{ id: string }>('/api/candidatures/', data)
    await loadCandidatures()
    return result
  }

  async function updateCandidature(
    id: string,
    data: { status?: string; notes?: string; current_step?: number; progress_pct?: number },
  ) {
    const result = await put<{ id: string; status: string }>(`/api/candidatures/${id}`, data)
    await loadCandidatures()
    return result
  }

  async function addHistoryEntry(id: string, action: string, details?: string) {
    await post(`/api/candidatures/${id}/history`, { action, details })
  }

  return {
    candidatures,
    currentDetail,
    stats,
    loading,
    loadingDetail,
    activeCount,
    activeCandidatures,
    loadCandidatures,
    loadStats,
    getCandidature,
    createCandidature,
    updateCandidature,
    addHistoryEntry,
  }
})
