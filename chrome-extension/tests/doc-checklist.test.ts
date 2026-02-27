import { describe, it, expect } from 'vitest'
import { validateDocument } from '../src/shared/doc-validator'
import type { RequiredDoc, DocumentSummary } from '../src/shared/types'

// === Helpers ===
function makeRequiredDoc(overrides: Partial<RequiredDoc> = {}): RequiredDoc {
  return {
    name: 'Rapport ESG',
    type: 'rapport_esg',
    format: 'pdf',
    description: 'Rapport ESG annuel',
    available_on_platform: false,
    document_id: null,
    ...overrides,
  }
}

function makeDocSummary(overrides: Partial<DocumentSummary> = {}): DocumentSummary {
  return {
    id: 'doc-1',
    nom_fichier: 'rapport_esg_2025.pdf',
    type_mime: 'application/pdf',
    taille: 500_000, // 500 Ko
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

// === validateDocument ===

describe('validateDocument', () => {
  it('retourne valid=true pour un document PDF correct et recent', () => {
    const doc = makeRequiredDoc({ format: 'pdf' })
    const available = makeDocSummary({ type_mime: 'application/pdf' })

    const result = validateDocument(doc, available)
    expect(result.valid).toBe(true)
    expect(result.warnings).toHaveLength(0)
  })

  it('retourne valid=false si le document est absent', () => {
    const doc = makeRequiredDoc()
    const result = validateDocument(doc, null)
    expect(result.valid).toBe(false)
    expect(result.warnings).toContain('Document non trouve')
  })

  it('avertit si le format ne correspond pas', () => {
    const doc = makeRequiredDoc({ format: 'pdf' })
    const available = makeDocSummary({ type_mime: 'image/png' })

    const result = validateDocument(doc, available)
    expect(result.valid).toBe(false)
    expect(result.warnings.length).toBeGreaterThan(0)
    expect(result.warnings[0]).toContain('Format attendu')
  })

  it('avertit si le fichier depasse 10 Mo', () => {
    const doc = makeRequiredDoc({ format: 'pdf' })
    const available = makeDocSummary({
      type_mime: 'application/pdf',
      taille: 15 * 1024 * 1024, // 15 Mo
    })

    const result = validateDocument(doc, available)
    expect(result.valid).toBe(false)
    expect(result.warnings.some(w => w.includes('volumineux'))).toBe(true)
  })

  it('n\'avertit pas pour un fichier de 9 Mo', () => {
    const doc = makeRequiredDoc({ format: 'pdf' })
    const available = makeDocSummary({
      type_mime: 'application/pdf',
      taille: 9 * 1024 * 1024,
    })

    const result = validateDocument(doc, available)
    expect(result.warnings.some(w => w.includes('volumineux'))).toBe(false)
  })

  it('avertit si le document a plus de 6 mois', () => {
    const doc = makeRequiredDoc({ format: 'pdf' })
    const sevenMonthsAgo = new Date()
    sevenMonthsAgo.setMonth(sevenMonthsAgo.getMonth() - 7)

    const available = makeDocSummary({
      type_mime: 'application/pdf',
      created_at: sevenMonthsAgo.toISOString(),
    })

    const result = validateDocument(doc, available)
    expect(result.warnings.some(w => w.includes('6 mois'))).toBe(true)
  })

  it('n\'avertit pas pour un document de 3 mois', () => {
    const doc = makeRequiredDoc({ format: 'pdf' })
    const threeMonthsAgo = new Date()
    threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3)

    const available = makeDocSummary({
      type_mime: 'application/pdf',
      created_at: threeMonthsAgo.toISOString(),
    })

    const result = validateDocument(doc, available)
    expect(result.warnings.some(w => w.includes('6 mois'))).toBe(false)
  })

  it('supporte les formats multiples (pdf,docx)', () => {
    const doc = makeRequiredDoc({ format: 'pdf,docx' })
    const available = makeDocSummary({ type_mime: 'application/pdf' })

    const result = validateDocument(doc, available)
    expect(result.warnings.some(w => w.includes('Format attendu'))).toBe(false)
  })

  it('accumule plusieurs warnings', () => {
    const doc = makeRequiredDoc({ format: 'pdf' })
    const eightMonthsAgo = new Date()
    eightMonthsAgo.setMonth(eightMonthsAgo.getMonth() - 8)

    const available = makeDocSummary({
      type_mime: 'image/png',
      taille: 12 * 1024 * 1024,
      created_at: eightMonthsAgo.toISOString(),
    })

    const result = validateDocument(doc, available)
    expect(result.valid).toBe(false)
    expect(result.warnings.length).toBe(3)
  })
})

// === ProgressBar computation ===

describe('Calcul progression globale', () => {
  function computeGlobalProgress(
    preStepDone: number, preStepCount: number,
    docReady: number, docTotal: number,
    currentStep: number, totalSteps: number,
  ): number {
    const total = preStepCount + docTotal + totalSteps
    if (total === 0) return 0
    const done = preStepDone + docReady + currentStep
    return Math.round((done / total) * 100)
  }

  it('retourne 0% si rien n\'est fait', () => {
    expect(computeGlobalProgress(0, 2, 0, 3, 0, 5)).toBe(0)
  })

  it('retourne 100% si tout est complete', () => {
    expect(computeGlobalProgress(2, 2, 3, 3, 5, 5)).toBe(100)
  })

  it('calcule correctement un cas mixte', () => {
    // 1/2 pre-etapes + 2/3 docs + 3/5 etapes = 6/10 = 60%
    expect(computeGlobalProgress(1, 2, 2, 3, 3, 5)).toBe(60)
  })

  it('retourne 0% si total est 0', () => {
    expect(computeGlobalProgress(0, 0, 0, 0, 0, 0)).toBe(0)
  })

  it('fonctionne sans pre-etapes', () => {
    // 0 pre-etapes + 2/4 docs + 3/6 etapes = 5/10 = 50%
    expect(computeGlobalProgress(0, 0, 2, 4, 3, 6)).toBe(50)
  })

  it('fonctionne sans documents', () => {
    // 1/2 pre-etapes + 0 docs + 2/4 etapes = 3/6 = 50%
    expect(computeGlobalProgress(1, 2, 0, 0, 2, 4)).toBe(50)
  })
})

// === DocWithStatus mapping ===

describe('Mapping documents avec statut', () => {
  const GENERATABLE_DOCS = [
    'rapport_esg',
    'fiche_entreprise',
    'bilan_carbone',
    'plan_action_esg',
  ]

  function mapDocsWithStatus(
    requiredDocs: RequiredDoc[],
    availableDocs: DocumentSummary[],
  ) {
    return requiredDocs.map(doc => {
      const matchedDoc = availableDocs.find(d =>
        d.nom_fichier.toLowerCase().includes(doc.type.toLowerCase()) ||
        d.type_mime?.includes(doc.format.toLowerCase())
      ) || null
      const isAvailable = doc.available_on_platform || !!matchedDoc
      return {
        ...doc,
        status: isAvailable ? 'ready' as const : 'missing' as const,
        can_generate: GENERATABLE_DOCS.includes(doc.type),
        matched_doc: matchedDoc,
      }
    })
  }

  it('marque un document disponible comme ready', () => {
    const docs = mapDocsWithStatus(
      [makeRequiredDoc({ available_on_platform: true })],
      [],
    )
    expect(docs[0].status).toBe('ready')
  })

  it('marque un document manquant comme missing', () => {
    const docs = mapDocsWithStatus(
      [makeRequiredDoc({ type: 'bilan_comptable' })],
      [],
    )
    expect(docs[0].status).toBe('missing')
  })

  it('detecte un document par nom de fichier', () => {
    const docs = mapDocsWithStatus(
      [makeRequiredDoc({ type: 'rapport_esg' })],
      [makeDocSummary({ nom_fichier: 'rapport_esg_2025.pdf' })],
    )
    expect(docs[0].status).toBe('ready')
    expect(docs[0].matched_doc).not.toBeNull()
  })

  it('identifie les documents generables', () => {
    const docs = mapDocsWithStatus(
      [
        makeRequiredDoc({ type: 'rapport_esg' }),
        makeRequiredDoc({ type: 'bilan_comptable' }),
      ],
      [],
    )
    expect(docs[0].can_generate).toBe(true)
    expect(docs[1].can_generate).toBe(false)
  })

  it('calcule readyCount correctement avec mix disponible/manquant', () => {
    const docs = mapDocsWithStatus(
      [
        makeRequiredDoc({ available_on_platform: true, type: 'fiche_entreprise' }),
        makeRequiredDoc({ type: 'bilan_comptable', format: 'xlsx' }),
        makeRequiredDoc({ type: 'rapport_esg', format: 'pdf' }),
      ],
      [makeDocSummary({ nom_fichier: 'rapport_esg.pdf', type_mime: 'application/pdf' })],
    )
    const readyCount = docs.filter(d => d.status === 'ready').length
    // fiche_entreprise: available_on_platform=true → ready
    // bilan_comptable: pas de match → missing
    // rapport_esg: match par nom_fichier → ready
    expect(readyCount).toBe(2)
  })
})
