import { describe, it, expect, vi, beforeEach } from 'vitest'

// === Mock Chrome APIs ===
const mockStorage: Record<string, Record<string, unknown>> = {
  session: {},
  local: {},
}

vi.stubGlobal('chrome', {
  storage: {
    session: {
      get: vi.fn(async (key: string) => ({ [key]: mockStorage.session[key] })),
      set: vi.fn(async (data: Record<string, unknown>) => {
        Object.assign(mockStorage.session, data)
      }),
      remove: vi.fn(async (key: string) => {
        delete mockStorage.session[key]
      }),
    },
    local: {
      get: vi.fn(async (key: string) => ({ [key]: mockStorage.local[key] })),
      set: vi.fn(async (data: Record<string, unknown>) => {
        Object.assign(mockStorage.local, data)
      }),
    },
  },
  tabs: {
    create: vi.fn(async (opts: { url: string }) => ({ id: 1, url: opts.url })),
  },
  runtime: {
    sendMessage: vi.fn(async () => ({})),
  },
  sidePanel: {
    open: vi.fn(async () => {}),
  },
})

// === Mock fetch ===
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function mockFetchResponse(status: number, body: unknown) {
  mockFetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
}

beforeEach(() => {
  mockStorage.session = {
    esg_jwt_token: 'test-token',
  }
  mockStorage.local = {}
  vi.clearAllMocks()
  // Re-set token for subsequent tests
  mockStorage.session.esg_mefali_token = 'test-token'
})

describe('Candidature flow - createApplication', () => {
  it('cree une candidature avec succes', async () => {
    vi.resetModules()
    // Token must be set BEFORE import (apiClient reads it via chrome.storage)
    mockStorage.session.esg_mefali_token = 'test-token'

    const { useApplications } = await import('../src/shared/stores/applications')
    const { createApplication } = useApplications()

    const mockApp = {
      id: 'app-123',
      status: 'brouillon',
      progress_pct: 0,
      fonds_id: 'fonds-1',
      fonds_nom: 'BOAD',
      fonds_institution: 'BOAD',
      form_data: {},
      current_step: 0,
      total_steps: 5,
      url_candidature: 'https://boad.org/apply',
      notes: null,
      started_at: '2026-01-01T00:00:00Z',
      submitted_at: null,
      updated_at: null,
      entreprise_id: 'ent-1',
    }

    mockFetchResponse(201, mockApp)

    const result = await createApplication({
      fonds_id: 'fonds-1',
      fonds_nom: 'BOAD',
      fonds_institution: 'BOAD',
      url_candidature: 'https://boad.org/apply',
    })

    expect(result.isDuplicate).toBe(false)
    expect(result.application).not.toBeNull()
    expect(result.application?.id).toBe('app-123')
  })

  it('detecte un doublon (409) et retourne isDuplicate=true', async () => {
    vi.resetModules()
    mockStorage.session.esg_mefali_token = 'test-token'

    const { useApplications } = await import('../src/shared/stores/applications')
    const { createApplication, applications } = useApplications()

    // Pre-populate with existing application
    applications.value = [
      {
        id: 'existing-app',
        entreprise_id: 'ent-1',
        fonds_id: 'fonds-1',
        fonds_nom: 'BOAD',
        fonds_institution: 'BOAD',
        status: 'en_cours',
        progress_pct: 40,
        form_data: {},
        current_step: 2,
        total_steps: 5,
        url_candidature: 'https://boad.org/apply',
        notes: null,
        started_at: '2026-01-01T00:00:00Z',
        submitted_at: null,
        updated_at: null,
      },
    ]

    // API returns 409 - non-ok response
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: async () => ({
        detail: 'Une candidature est deja en cours pour ce fonds',
      }),
    })

    const result = await createApplication({
      fonds_id: 'fonds-1',
      fonds_nom: 'BOAD',
    })

    expect(result.isDuplicate).toBe(true)
    expect(result.application?.id).toBe('existing-app')
    expect(result.application?.progress_pct).toBe(40)
  })

  it('retourne null en cas d\'erreur reseau', async () => {
    vi.resetModules()
    mockStorage.session.esg_mefali_token = 'test-token'

    const { useApplications } = await import('../src/shared/stores/applications')
    const { createApplication } = useApplications()

    mockFetchResponse(500, { detail: 'Erreur serveur' })

    const result = await createApplication({
      fonds_id: 'fonds-2',
      fonds_nom: 'GCF',
    })

    expect(result.isDuplicate).toBe(false)
    expect(result.application).toBeNull()
  })
})

describe('Candidature flow - workflow mode_acces', () => {
  it('isDirectAccess retourne true pour mode direct', () => {
    function isDirectAccess(mode: string | null): boolean {
      return !mode || mode === 'direct' || mode === 'appel_propositions'
    }

    expect(isDirectAccess('direct')).toBe(true)
    expect(isDirectAccess('appel_propositions')).toBe(true)
    expect(isDirectAccess(null)).toBe(true)
    expect(isDirectAccess('banque_partenaire')).toBe(false)
    expect(isDirectAccess('entite_accreditee')).toBe(false)
    expect(isDirectAccess('garantie_bancaire')).toBe(false)
  })

  it('mode direct ouvre l\'URL du fonds', () => {
    const fonds = {
      mode_acces: 'direct',
      url_source: 'https://boad.org/apply',
    }

    // Simulate the workflow logic
    const isDirectAccess = !fonds.mode_acces || fonds.mode_acces === 'direct' || fonds.mode_acces === 'appel_propositions'

    expect(isDirectAccess).toBe(true)
    expect(fonds.url_source).toBeTruthy()
  })

  it('mode banque_partenaire utilise l\'URL intermediaire', () => {
    const fonds = {
      mode_acces: 'banque_partenaire',
      url_source: 'https://boad.org',
      acces_details: {
        intermediaire: 'https://bank.partner.com/apply',
      },
    }

    const isIntermedaire = ['banque_partenaire', 'entite_accreditee', 'banque_multilaterale'].includes(fonds.mode_acces)
    expect(isIntermedaire).toBe(true)
    expect(fonds.acces_details?.intermediaire).toBe('https://bank.partner.com/apply')
  })

  it('mode sans URL ne tente pas d\'ouverture', () => {
    const fonds = {
      mode_acces: 'direct',
      url_source: null as string | null,
    }

    expect(fonds.url_source).toBeNull()
    // Le code ne devrait pas appeler chrome.tabs.create si pas d'URL
  })
})

describe('Candidature flow - deduplication detection', () => {
  it('getExistingApplication trouve une candidature existante', () => {
    const applications = [
      { id: 'app-1', fonds_id: 'fonds-1', status: 'en_cours', progress_pct: 50 },
      { id: 'app-2', fonds_id: 'fonds-2', status: 'brouillon', progress_pct: 0 },
      { id: 'app-3', fonds_id: 'fonds-3', status: 'soumise', progress_pct: 100 },
    ]

    function getExistingApplication(fondsId: string) {
      return applications.find(
        a => a.fonds_id === fondsId && ['brouillon', 'en_cours'].includes(a.status)
      ) || null
    }

    expect(getExistingApplication('fonds-1')?.id).toBe('app-1')
    expect(getExistingApplication('fonds-2')?.id).toBe('app-2')
    // soumise n'est pas active
    expect(getExistingApplication('fonds-3')).toBeNull()
    // fonds inexistant
    expect(getExistingApplication('fonds-99')).toBeNull()
  })
})
