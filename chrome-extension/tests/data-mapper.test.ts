import { describe, it, expect } from 'vitest'
import { DataMapper } from '../src/shared/data-mapper'

describe('DataMapper', () => {
  const mockData = {
    user: { id: '1', email: 'test@test.com', nom_complet: 'Test User', role: 'user', is_active: true },
    entreprise: {
      id: '1',
      nom: 'AgroVert CI',
      secteur: 'agriculture',
      sous_secteur: null,
      pays: "Cote d'Ivoire",
      ville: null,
      effectifs: 45,
      chiffre_affaires: 150000000,
      devise: 'XOF',
      description: 'PME agroalimentaire bio',
      profil_json: null,
    },
    scores: [
      { id: '1', score_e: 72, score_s: 65, score_g: 58, score_global: 66, referentiel_code: 'bceao_fd_2024', created_at: '2026-01-15' },
    ],
    documents: [
      { id: '1', nom_fichier: 'bilan_2025.pdf', type_mime: 'application/pdf', taille: 245000, created_at: '2026-01-10' },
    ],
    fonds_recommandes: [],
    applications: [],
    last_synced: '2026-02-15T10:00:00Z',
  }

  it('resout un chemin simple', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('entreprise.nom')).toBe('AgroVert CI')
    expect(mapper.resolve('entreprise.pays')).toBe("Cote d'Ivoire")
    expect(mapper.resolve('entreprise.effectifs')).toBe('45')
  })

  it('resout un chemin avec formatter', () => {
    const mapper = new DataMapper(mockData as never)
    const result = mapper.resolve('entreprise.chiffre_affaires|format_currency')
    expect(result).toContain('150')
  })

  it('resout les scores', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('scores.latest.score_global')).toBe('66')
  })

  it('resout les sous-scores', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('scores.latest.score_e')).toBe('72')
    expect(mapper.resolve('scores.latest.score_s')).toBe('65')
    expect(mapper.resolve('scores.latest.score_g')).toBe('58')
  })

  it('resout les donnees utilisateur', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('user.email')).toBe('test@test.com')
    expect(mapper.resolve('user.nom_complet')).toBe('Test User')
  })

  it('retourne null pour un chemin inexistant', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('entreprise.adresse')).toBeNull()
    expect(mapper.resolve('inexistant.path')).toBeNull()
  })

  it('retourne null pour un source vide', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('')).toBeNull()
  })

  it('applique le formatter format_percentage', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('scores.latest.score_global|format_percentage')).toBe('66.0%')
  })

  it('applique le formatter uppercase', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('entreprise.pays|uppercase')).toBe("COTE D'IVOIRE")
  })

  it('applique le formatter lowercase', () => {
    const mapper = new DataMapper(mockData as never)
    expect(mapper.resolve('entreprise.nom|lowercase')).toBe('agrovert ci')
  })

  it('mappe une etape complete', () => {
    const mapper = new DataMapper(mockData as never)
    const result = mapper.mapStep([
      { selector: '#company-name', source: 'entreprise.nom' },
      { selector: '#sector', source: 'entreprise.secteur' },
      { selector: '#description', source: null },
      { selector: '#missing', source: 'entreprise.adresse' },
    ])
    expect(result['#company-name']).toBe('AgroVert CI')
    expect(result['#sector']).toBe('agriculture')
    expect(result['#description']).toBeUndefined()
    expect(result['#missing']).toBeUndefined()
  })

  it('gere les scores vides', () => {
    const emptyScoresData = { ...mockData, scores: [] }
    const mapper = new DataMapper(emptyScoresData as never)
    expect(mapper.resolve('scores.latest.score_global')).toBeNull()
  })

  it('gere une entreprise null', () => {
    const noEntrepriseData = { ...mockData, entreprise: null }
    const mapper = new DataMapper(noEntrepriseData as never)
    expect(mapper.resolve('entreprise.nom')).toBeNull()
  })
})
