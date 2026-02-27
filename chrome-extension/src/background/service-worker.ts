import { authManager } from '@shared/auth'
import { apiClient } from '@shared/api-client'
import { storageManager } from '@shared/storage'
import { checkDeadlinesAndReminders } from './notifications'
import type {
  ExtensionMessage,
  SyncedData,
  Entreprise,
  FundSiteConfig,
  FundApplication,
} from '@shared/types'

// ========================================
// Initialisation
// ========================================

chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === 'install') {
    console.log('[ESG Mefali] Extension installee')
  }
  // Verifier les deadlines au demarrage
  checkDeadlinesAndReminders()
})

chrome.runtime.onStartup.addListener(() => {
  checkDeadlinesAndReminders()
})

// ========================================
// Gestion des messages
// ========================================

chrome.runtime.onMessage.addListener((message: ExtensionMessage, sender, sendResponse) => {
  handleMessage(message, sender).then(sendResponse)
  return true
})

async function handleMessage(
  message: ExtensionMessage,
  sender: chrome.runtime.MessageSender
): Promise<unknown> {
  switch (message.type) {
    case 'AUTH_STATUS':
      return handleAuthStatus()

    case 'SYNC_DATA':
      return handleSyncData()

    case 'FUND_DETECTED':
      return handleFundDetected(message.payload as { url: string, tabId: number }, sender)

    case 'GET_COMPANY_DATA':
      return handleGetCompanyData()

    case 'FIELD_SUGGESTION':
      return handleFieldSuggestion(message.payload as {
        fonds_id: string
        field_name: string
        field_label: string
        context: string
      })

    case 'SAVE_PROGRESS':
      return handleSaveProgress(message.payload as {
        application_id: string
        form_data: Record<string, unknown>
        current_step: number
      })

    case 'OPEN_SIDEPANEL':
      return handleOpenSidePanel(sender)

    case 'GET_FUND_CONFIGS':
      return handleGetFundConfigs()

    case 'OPEN_FUND_APPLICATION':
      return handleOpenFundApplication(message.payload as {
        url: string
        fonds_id: string
        intermediaire_id?: string
        application_data?: Record<string, unknown>
      })

    case 'GET_APPLICATION_PROGRESS':
      return handleGetApplicationProgress(message.payload as {
        application_id: string
      })

    default:
      console.warn('[ESG Mefali] Message inconnu:', message.type)
      return null
  }
}

// ========================================
// Handlers
// ========================================

async function handleAuthStatus() {
  const user = await authManager.checkAuth()
  return { authenticated: !!user, user }
}

async function handleSyncData(): Promise<SyncedData | null> {
  const cached = await storageManager.getSyncedData()
  if (cached) return cached

  try {
    const user = await authManager.checkAuth()
    if (!user) return null

    const [entreprises, applications] = await Promise.all([
      apiClient.get<Entreprise[]>('/api/entreprises/'),
      apiClient.get<FundApplication[]>('/api/extension/applications').catch(() => []),
    ])

    const entreprise = entreprises[0] || null

    let scores: unknown[] = []
    let documents: unknown[] = []
    let fonds: unknown[] = []

    if (entreprise) {
      ;[scores, documents, fonds] = await Promise.all([
        apiClient.get(`/api/entreprises/${entreprise.id}/scores`).catch(() => []),
        apiClient.get(`/api/documents/entreprise/${entreprise.id}`).catch(() => []),
        apiClient.get('/api/extension/fund-recommendations').catch(() => []),
      ])
    }

    const syncedData = {
      user,
      entreprise,
      scores: scores as SyncedData['scores'],
      documents: documents as SyncedData['documents'],
      fonds_recommandes: fonds as SyncedData['fonds_recommandes'],
      applications: applications as SyncedData['applications'],
    }

    await storageManager.saveSyncedData(syncedData)
    return { ...syncedData, last_synced: new Date().toISOString() }
  } catch (error) {
    console.error('[ESG Mefali] Erreur de synchronisation:', error)
    return null
  }
}

async function handleFundDetected(
  payload: { url: string; tabId?: number },
  sender: chrome.runtime.MessageSender
) {
  const tabId = payload.tabId || sender.tab?.id
  const configs = await getFundConfigs()
  const matchedConfig = configs.find(config =>
    config.url_patterns.some(pattern => matchUrl(payload.url, pattern))
  )

  if (matchedConfig) {
    if (tabId) {
      chrome.action.setBadgeText({ text: '!', tabId })
      chrome.action.setBadgeBackgroundColor({ color: '#059669', tabId })
    }

    chrome.notifications.create(`fund-${matchedConfig.fonds_id}`, {
      type: 'basic',
      iconUrl: 'assets/icons/icon-128.png',
      title: 'Fonds vert detecte !',
      message: `${matchedConfig.fonds_nom} - Cliquez pour etre guide dans votre candidature`,
    })

    return { detected: true, config: matchedConfig }
  }

  return { detected: false }
}

async function handleGetCompanyData() {
  const data = await storageManager.getSyncedData()
  if (!data) {
    return handleSyncData()
  }
  return data
}

async function handleFieldSuggestion(payload: {
  fonds_id: string
  field_name: string
  field_label: string
  context: string
}) {
  try {
    const response = await apiClient.post<{ suggestion: string }>(
      '/api/extension/field-suggest',
      payload
    )
    return response
  } catch (error) {
    console.error('[ESG Mefali] Erreur suggestion:', error)
    return { suggestion: null, error: 'Impossible de generer une suggestion' }
  }
}

async function handleSaveProgress(payload: {
  application_id: string
  form_data: Record<string, unknown>
  current_step: number
}) {
  try {
    return await apiClient.post('/api/extension/progress', payload)
  } catch (error) {
    console.error('[ESG Mefali] Erreur sauvegarde:', error)
    return { error: 'Impossible de sauvegarder' }
  }
}

async function handleOpenSidePanel(sender: chrome.runtime.MessageSender) {
  const tab = sender.tab || (await chrome.tabs.query({ active: true, currentWindow: true }))[0]
  if (tab?.id) {
    chrome.sidePanel.open({ tabId: tab.id })
  }
  return { ok: true }
}

async function handleGetFundConfigs() {
  const configs = await getFundConfigs()
  return { configs }
}

async function handleOpenFundApplication(payload: {
  url: string
  fonds_id: string
  intermediaire_id?: string
  application_data?: Record<string, unknown>
}) {
  try {
    const tab = await chrome.tabs.create({ url: payload.url })

    await chrome.storage.session.set({
      pending_fund_application: {
        fonds_id: payload.fonds_id,
        intermediaire_id: payload.intermediaire_id,
        tab_id: tab.id,
        application_data: payload.application_data,
      },
    })

    if (tab.id) {
      await chrome.sidePanel.open({ tabId: tab.id })
    }

    return { opened: true, tab_id: tab.id }
  } catch (error) {
    console.error('[ESG Mefali] Erreur ouverture candidature:', error)
    return { opened: false, error: String(error) }
  }
}

async function handleGetApplicationProgress(payload: { application_id: string }) {
  try {
    const app = await apiClient.get<FundApplication>(
      `/api/extension/applications/${payload.application_id}`
    )
    return app
  } catch (error) {
    console.error('[ESG Mefali] Erreur récupération progression:', error)
    return { error: String(error) }
  }
}

// ========================================
// Utilitaires
// ========================================

async function getFundConfigs(): Promise<FundSiteConfig[]> {
  const cached = await storageManager.getFundConfigs()
  if (cached) return cached

  try {
    const configs = await apiClient.get<FundSiteConfig[]>('/api/extension/fund-configs')
    await storageManager.saveFundConfigs(configs)
    return configs
  } catch {
    return []
  }
}

function matchUrl(url: string, pattern: string): boolean {
  const regex = new RegExp(
    '^' + pattern
      .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
      .replace(/\*/g, '.*')
    + '$'
  )
  return regex.test(url)
}

// ========================================
// Alarmes periodiques
// ========================================

chrome.alarms.create('check-auth', { periodInMinutes: 30 })
chrome.alarms.create('sync-data', { periodInMinutes: 5 })
chrome.alarms.create('check-deadlines', { periodInMinutes: 360 })

chrome.alarms.onAlarm.addListener(async (alarm) => {
  switch (alarm.name) {
    case 'check-auth':
      await authManager.checkAuth()
      break
    case 'sync-data':
      await handleSyncData()
      break
    case 'check-deadlines':
      await checkDeadlinesAndReminders()
      break
  }
})

chrome.notifications.onClicked.addListener(async (notificationId) => {
  if (notificationId.startsWith('fund-')) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (tab?.id) {
      chrome.sidePanel.open({ tabId: tab.id })
    }
  }
})
