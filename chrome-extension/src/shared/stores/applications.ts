import { ref, computed } from 'vue'
import { apiClient, ApiError } from '../api-client'
import type { FundApplication } from '../types'

const applications = ref<FundApplication[]>([])
const loading = ref(false)

export function useApplications() {
  const activeApplications = computed(() =>
    applications.value.filter(a => ['brouillon', 'en_cours'].includes(a.status))
  )

  const completedApplications = computed(() =>
    applications.value.filter(a => ['soumise', 'acceptee', 'refusee'].includes(a.status))
  )

  async function loadApplications() {
    loading.value = true
    try {
      applications.value = await apiClient.get<FundApplication[]>('/api/extension/applications')
    } catch (error) {
      console.error('Erreur chargement candidatures:', error)
    } finally {
      loading.value = false
    }
  }

  async function createApplication(data: {
    fonds_id?: string
    fonds_nom: string
    fonds_institution?: string
    url_candidature?: string
    total_steps?: number
    notes?: string
  }): Promise<FundApplication | null> {
    try {
      const app = await apiClient.post<FundApplication>('/api/extension/applications', data)
      applications.value.unshift(app)
      return app
    } catch (error) {
      console.error('Erreur creation candidature:', error)
      return null
    }
  }

  async function updateApplication(
    id: string,
    updates: Partial<FundApplication>
  ): Promise<void> {
    try {
      const updated = await apiClient.put<FundApplication>(
        `/api/extension/applications/${id}`,
        updates
      )
      const index = applications.value.findIndex(a => a.id === id)
      if (index >= 0) {
        applications.value[index] = updated
      }
    } catch (error) {
      console.error('Erreur mise a jour candidature:', error)
    }
  }

  async function saveProgress(
    applicationId: string,
    formData: Record<string, unknown>,
    currentStep: number,
    progressPct: number
  ) {
    try {
      await apiClient.post('/api/extension/progress', {
        application_id: applicationId,
        form_data: formData,
        current_step: currentStep,
        progress_pct: progressPct,
      })
    } catch (error) {
      console.error('Erreur sauvegarde progression:', error)
    }
  }

  return {
    applications,
    activeApplications,
    completedApplications,
    loading,
    loadApplications,
    createApplication,
    updateApplication,
    saveProgress,
  }
}
