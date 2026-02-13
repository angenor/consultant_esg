import { ref } from 'vue'
import { defineStore } from 'pinia'
import { useApi } from '../composables/useApi'

// ==================== Skill ====================

export interface Skill {
  id: string
  nom: string
  description: string
  category: string | null
  input_schema: Record<string, unknown>
  handler_key: string
  handler_code: string | null
  is_active: boolean
  version: number
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface SkillTestResult {
  success: boolean
  result: Record<string, unknown> | null
  error: string | null
  duration_ms: number | null
}

// ==================== Referentiel ====================

export interface Referentiel {
  id: string
  nom: string
  code: string
  institution: string | null
  description: string | null
  region: string | null
  grille_json: GrilleESG
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface GrilleESG {
  methode_aggregation: string
  piliers: Record<string, PilierData>
}

export interface PilierData {
  poids_global: number
  criteres: CritereData[]
}

export interface CritereData {
  id: string
  label: string
  poids: number
  type: 'quantitatif' | 'qualitatif'
  unite?: string
  seuils?: Record<string, { min?: number; max?: number; score: number }>
  options?: { label: string; score: number }[]
  question_collecte?: string
}

export interface ScorePreviewResult {
  score_global: number
  niveau: string
  piliers: Record<
    string,
    {
      poids_global: number
      score: number
      criteres: {
        critere_id: string
        label: string
        score: number
        status: string
        valeur: string | null
      }[]
    }
  >
}

// ==================== Fonds ====================

export interface Fonds {
  id: string
  nom: string
  institution: string | null
  type: string | null
  referentiel_id: string | null
  montant_min: number | null
  montant_max: number | null
  devise: string
  secteurs_json: string[] | null
  pays_eligibles: string[] | null
  criteres_json: Record<string, unknown> | null
  date_limite: string | null
  url_source: string | null
  is_active: boolean
  created_at: string
}

// ==================== Template ====================

export interface ReportTemplate {
  id: string
  nom: string
  description: string | null
  sections_json: Record<string, unknown>
  template_html: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// ==================== Stats ====================

export interface DashboardStats {
  users: number
  entreprises: number
  conversations: number
  scores_esg: number
  skills: { total: number; active: number }
  referentiels: number
  fonds_verts: number
}

// ==================== Store ====================

export const useAdminStore = defineStore('admin', () => {
  const api = useApi()

  // --------------- State ---------------
  const skills = ref<Skill[]>([])
  const referentiels = ref<Referentiel[]>([])
  const fonds = ref<Fonds[]>([])
  const templates = ref<ReportTemplate[]>([])
  const stats = ref<DashboardStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ===================== Skills =====================

  async function loadSkills(filters?: { category?: string; is_active?: boolean; search?: string }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (filters?.category) params.set('category', filters.category)
      if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active))
      if (filters?.search) params.set('search', filters.search)
      const qs = params.toString()
      skills.value = await api.get<Skill[]>(`/api/admin/skills/${qs ? '?' + qs : ''}`)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erreur lors du chargement'
    } finally {
      loading.value = false
    }
  }

  async function getSkill(id: string): Promise<Skill> {
    return api.get<Skill>(`/api/admin/skills/${id}`)
  }

  async function createSkill(data: {
    nom: string
    description: string
    category: string
    input_schema: Record<string, unknown>
    handler_key: string
    handler_code?: string | null
  }): Promise<Skill> {
    const skill = await api.post<Skill>('/api/admin/skills/', data)
    await loadSkills()
    return skill
  }

  async function updateSkill(
    id: string,
    data: {
      description?: string
      category?: string
      input_schema?: Record<string, unknown>
      handler_code?: string
      is_active?: boolean
    },
  ): Promise<Skill> {
    const skill = await api.put<Skill>(`/api/admin/skills/${id}`, data)
    await loadSkills()
    return skill
  }

  async function deleteSkill(id: string): Promise<void> {
    await api.del(`/api/admin/skills/${id}`)
    await loadSkills()
  }

  async function toggleSkill(id: string): Promise<Skill> {
    const skill = await api.post<Skill>(`/api/admin/skills/${id}/toggle`)
    await loadSkills()
    return skill
  }

  async function testSkill(id: string, params: Record<string, unknown>): Promise<SkillTestResult> {
    return api.post<SkillTestResult>(`/api/admin/skills/${id}/test`, { params })
  }

  // ===================== Referentiels =====================

  async function loadReferentiels(filters?: { region?: string; is_active?: boolean; search?: string }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (filters?.region) params.set('region', filters.region)
      if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active))
      if (filters?.search) params.set('search', filters.search)
      const qs = params.toString()
      referentiels.value = await api.get<Referentiel[]>(`/api/admin/referentiels/${qs ? '?' + qs : ''}`)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erreur lors du chargement'
    } finally {
      loading.value = false
    }
  }

  async function getReferentiel(id: string): Promise<Referentiel> {
    return api.get<Referentiel>(`/api/admin/referentiels/${id}`)
  }

  async function createReferentiel(data: {
    nom: string
    code: string
    institution?: string | null
    description?: string | null
    region?: string | null
    grille_json: Record<string, unknown>
  }): Promise<Referentiel> {
    const ref = await api.post<Referentiel>('/api/admin/referentiels/', data)
    await loadReferentiels()
    return ref
  }

  async function updateReferentiel(id: string, data: Record<string, unknown>): Promise<Referentiel> {
    const ref = await api.put<Referentiel>(`/api/admin/referentiels/${id}`, data)
    await loadReferentiels()
    return ref
  }

  async function deleteReferentiel(id: string): Promise<void> {
    await api.del(`/api/admin/referentiels/${id}`)
    await loadReferentiels()
  }

  async function toggleReferentiel(id: string): Promise<Referentiel> {
    const ref = await api.post<Referentiel>(`/api/admin/referentiels/${id}/toggle`)
    await loadReferentiels()
    return ref
  }

  async function previewScoring(id: string, reponses: Record<string, unknown>): Promise<ScorePreviewResult> {
    return api.post<ScorePreviewResult>(`/api/admin/referentiels/${id}/preview`, { reponses })
  }

  // ===================== Fonds =====================

  async function loadFonds(filters?: { is_active?: boolean; search?: string }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active))
      if (filters?.search) params.set('search', filters.search)
      const qs = params.toString()
      fonds.value = await api.get<Fonds[]>(`/api/admin/fonds/${qs ? '?' + qs : ''}`)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erreur lors du chargement'
    } finally {
      loading.value = false
    }
  }

  async function getFonds(id: string): Promise<Fonds> {
    return api.get<Fonds>(`/api/admin/fonds/${id}`)
  }

  async function createFonds(data: Record<string, unknown>): Promise<Fonds> {
    const f = await api.post<Fonds>('/api/admin/fonds/', data)
    await loadFonds()
    return f
  }

  async function updateFonds(id: string, data: Record<string, unknown>): Promise<Fonds> {
    const f = await api.put<Fonds>(`/api/admin/fonds/${id}`, data)
    await loadFonds()
    return f
  }

  async function deleteFonds(id: string): Promise<void> {
    await api.del(`/api/admin/fonds/${id}`)
    await loadFonds()
  }

  // ===================== Templates =====================

  async function loadTemplates(filters?: { is_active?: boolean; search?: string }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active))
      if (filters?.search) params.set('search', filters.search)
      const qs = params.toString()
      templates.value = await api.get<ReportTemplate[]>(`/api/admin/templates/${qs ? '?' + qs : ''}`)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erreur lors du chargement'
    } finally {
      loading.value = false
    }
  }

  async function getTemplate(id: string): Promise<ReportTemplate> {
    return api.get<ReportTemplate>(`/api/admin/templates/${id}`)
  }

  async function createTemplate(data: Record<string, unknown>): Promise<ReportTemplate> {
    const t = await api.post<ReportTemplate>('/api/admin/templates/', data)
    await loadTemplates()
    return t
  }

  async function updateTemplate(id: string, data: Record<string, unknown>): Promise<ReportTemplate> {
    const t = await api.put<ReportTemplate>(`/api/admin/templates/${id}`, data)
    await loadTemplates()
    return t
  }

  async function deleteTemplate(id: string): Promise<void> {
    await api.del(`/api/admin/templates/${id}`)
    await loadTemplates()
  }

  // ===================== Stats =====================

  async function loadStats(): Promise<DashboardStats> {
    const data = await api.get<DashboardStats>('/api/admin/stats/dashboard')
    stats.value = data
    return data
  }

  return {
    // State
    skills,
    referentiels,
    fonds,
    templates,
    stats,
    loading,
    error,
    // Skills
    loadSkills,
    getSkill,
    createSkill,
    updateSkill,
    deleteSkill,
    toggleSkill,
    testSkill,
    // Referentiels
    loadReferentiels,
    getReferentiel,
    createReferentiel,
    updateReferentiel,
    deleteReferentiel,
    toggleReferentiel,
    previewScoring,
    // Fonds
    loadFonds,
    getFonds,
    createFonds,
    updateFonds,
    deleteFonds,
    // Templates
    loadTemplates,
    getTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    // Stats
    loadStats,
  }
})
