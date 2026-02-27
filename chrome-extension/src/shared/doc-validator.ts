import type { RequiredDoc, DocumentSummary, DocValidation } from './types'

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 Mo
const STALE_THRESHOLD = 180 * 24 * 60 * 60 * 1000 // 6 mois

export function validateDocument(
  doc: RequiredDoc,
  available: DocumentSummary | null,
): DocValidation {
  const warnings: string[] = []

  if (!available) {
    return { valid: false, warnings: ['Document non trouve'] }
  }

  // Verification format
  const expectedFormats = doc.format.split(',').map(f => f.trim().toLowerCase())
  const actualFormat = available.type_mime?.split('/')[1]?.toLowerCase() || ''
  if (expectedFormats.length && !expectedFormats.some(f => actualFormat.includes(f))) {
    warnings.push(`Format attendu : ${doc.format}, recu : ${actualFormat}`)
  }

  // Verification taille (max 10 Mo)
  if (available.taille > MAX_FILE_SIZE) {
    warnings.push(`Fichier trop volumineux (${(available.taille / 1024 / 1024).toFixed(1)} Mo, max 10 Mo)`)
  }

  // Verification anciennete (alerte si > 6 mois)
  if (Date.now() - new Date(available.created_at).getTime() > STALE_THRESHOLD) {
    warnings.push('Document date de plus de 6 mois — verifiez sa validite')
  }

  return { valid: warnings.length === 0, warnings }
}
