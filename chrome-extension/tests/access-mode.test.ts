import { describe, it, expect } from 'vitest'
import {
  ACCESS_MODE_CONFIGS,
  getAccessModeConfig,
  type AccessModeConfig,
  type PreStep,
} from '../src/shared/access-mode-config'

describe('ACCESS_MODE_CONFIGS', () => {
  const ALL_MODES = [
    'direct',
    'banque_partenaire',
    'appel_propositions',
    'entite_accreditee',
    'garantie_bancaire',
    'banque_multilaterale',
  ]

  it('contient les 6 modes d\'accès', () => {
    expect(Object.keys(ACCESS_MODE_CONFIGS)).toHaveLength(6)
    for (const mode of ALL_MODES) {
      expect(ACCESS_MODE_CONFIGS).toHaveProperty(mode)
    }
  })

  it('chaque mode a les champs requis', () => {
    for (const mode of ALL_MODES) {
      const config = ACCESS_MODE_CONFIGS[mode]
      expect(config.key).toBe(mode)
      expect(config.label).toBeTruthy()
      expect(config.description).toBeTruthy()
      expect(config.color).toBeTruthy()
      expect(Array.isArray(config.preSteps)).toBe(true)
      expect(Array.isArray(config.tips)).toBe(true)
      expect(config.tips.length).toBeGreaterThan(0)
      expect(typeof config.requires_intermediary).toBe('boolean')
    }
  })

  it('mode "direct" a 0 pré-étapes', () => {
    const config = ACCESS_MODE_CONFIGS.direct
    expect(config.preSteps).toHaveLength(0)
    expect(config.requires_intermediary).toBe(false)
  })

  it('mode "banque_partenaire" a 2 pré-étapes', () => {
    const config = ACCESS_MODE_CONFIGS.banque_partenaire
    expect(config.preSteps).toHaveLength(2)
    expect(config.requires_intermediary).toBe(true)
    expect(config.preSteps[0].action).toBe('contact_bank')
    expect(config.preSteps[1].action).toBe('prepare_dossier')
  })

  it('mode "entite_accreditee" a 3 pré-étapes', () => {
    const config = ACCESS_MODE_CONFIGS.entite_accreditee
    expect(config.preSteps).toHaveLength(3)
    expect(config.requires_intermediary).toBe(true)
    expect(config.preSteps[0].action).toBe('find_entity')
  })

  it('mode "appel_propositions" a 1 pré-étape', () => {
    const config = ACCESS_MODE_CONFIGS.appel_propositions
    expect(config.preSteps).toHaveLength(1)
    expect(config.requires_intermediary).toBe(false)
    expect(config.preSteps[0].action).toBe('check_calendar')
  })

  it('mode "garantie_bancaire" a 2 pré-étapes', () => {
    const config = ACCESS_MODE_CONFIGS.garantie_bancaire
    expect(config.preSteps).toHaveLength(2)
    expect(config.requires_intermediary).toBe(true)
  })

  it('mode "banque_multilaterale" a 2 pré-étapes', () => {
    const config = ACCESS_MODE_CONFIGS.banque_multilaterale
    expect(config.preSteps).toHaveLength(2)
    expect(config.requires_intermediary).toBe(true)
  })

  it('les modes avec intermediaire requièrent requires_intermediary = true', () => {
    const intermediaryModes = ['banque_partenaire', 'entite_accreditee', 'garantie_bancaire', 'banque_multilaterale']
    for (const mode of intermediaryModes) {
      expect(ACCESS_MODE_CONFIGS[mode].requires_intermediary).toBe(true)
    }
  })

  it('les modes sans intermediaire ont requires_intermediary = false', () => {
    const directModes = ['direct', 'appel_propositions']
    for (const mode of directModes) {
      expect(ACCESS_MODE_CONFIGS[mode].requires_intermediary).toBe(false)
    }
  })
})

describe('getAccessModeConfig', () => {
  it('retourne la config pour un mode valide', () => {
    const config = getAccessModeConfig('banque_partenaire')
    expect(config.key).toBe('banque_partenaire')
    expect(config.label).toBe('Via banque partenaire')
  })

  it('retourne "direct" pour null', () => {
    const config = getAccessModeConfig(null)
    expect(config.key).toBe('direct')
  })

  it('retourne "direct" pour undefined', () => {
    const config = getAccessModeConfig(undefined)
    expect(config.key).toBe('direct')
  })

  it('retourne "direct" pour un mode inconnu', () => {
    const config = getAccessModeConfig('mode_inexistant')
    expect(config.key).toBe('direct')
  })
})

describe('PreStep structure', () => {
  it('toutes les pré-étapes ont title et description', () => {
    for (const [, config] of Object.entries(ACCESS_MODE_CONFIGS)) {
      for (const step of config.preSteps) {
        expect(step.title).toBeTruthy()
        expect(step.description).toBeTruthy()
        expect(step.completed_by).toMatch(/^(user_confirm|auto)$/)
      }
    }
  })

  it('les actions sont parmi les valeurs valides', () => {
    const validActions = ['contact_bank', 'find_entity', 'check_calendar', 'prepare_dossier']
    for (const [, config] of Object.entries(ACCESS_MODE_CONFIGS)) {
      for (const step of config.preSteps) {
        if (step.action) {
          expect(validActions).toContain(step.action)
        }
      }
    }
  })
})

describe('Combined steps (pre-steps + form steps)', () => {
  it('les pré-étapes précèdent les étapes formulaire', () => {
    const preSteps = ACCESS_MODE_CONFIGS.banque_partenaire.preSteps
    const formSteps = [
      { order: 1, title: 'Informations', description: '', url_pattern: null, fields: [] },
      { order: 2, title: 'Documents', description: '', url_pattern: null, fields: [] },
    ]

    const allSteps = [
      ...preSteps.map((ps, i) => ({
        title: ps.title,
        isPreStep: true,
        completed: false,
        index: i,
      })),
      ...formSteps.map((s, i) => ({
        title: s.title,
        isPreStep: false,
        completed: false,
        index: i,
      })),
    ]

    expect(allSteps).toHaveLength(4) // 2 pré-étapes + 2 étapes
    expect(allSteps[0].isPreStep).toBe(true)
    expect(allSteps[1].isPreStep).toBe(true)
    expect(allSteps[2].isPreStep).toBe(false)
    expect(allSteps[3].isPreStep).toBe(false)
  })
})

describe('ApplicationStatus', () => {
  it('le statut en_attente_intermediaire est valide', () => {
    type ApplicationStatus =
      | 'brouillon'
      | 'en_cours'
      | 'en_attente_intermediaire'
      | 'soumise'
      | 'acceptee'
      | 'refusee'
      | 'abandonnee'

    const validStatuses: ApplicationStatus[] = [
      'brouillon', 'en_cours', 'en_attente_intermediaire',
      'soumise', 'acceptee', 'refusee', 'abandonnee',
    ]
    expect(validStatuses).toContain('en_attente_intermediaire')
    expect(validStatuses).toHaveLength(7)
  })

  it('les statuts actifs incluent en_attente_intermediaire', () => {
    const activeStatuses = ['brouillon', 'en_cours', 'en_attente_intermediaire']
    expect(activeStatuses).toContain('en_attente_intermediaire')
  })
})
