import type { ESGScore, SyncedData } from './types'

/**
 * Mappe les donnees de la plateforme vers les champs des formulaires de fonds.
 *
 * Le `source` dans la config du fonds peut etre :
 * - Un chemin direct : "entreprise.nom", "entreprise.pays"
 * - Un chemin calcule : "scores.latest.score_global"
 * - Une reference formatee : "entreprise.chiffre_affaires|format_currency"
 */
export class DataMapper {
  private data: SyncedData
  private formatters: Record<string, (value: unknown) => string>

  constructor(data: SyncedData) {
    this.data = data

    this.formatters = {
      format_currency: (v) => {
        const num = Number(v)
        if (isNaN(num)) return String(v)
        return new Intl.NumberFormat('fr-FR').format(num)
      },
      format_date_fr: (v) => {
        const d = new Date(String(v))
        return d.toLocaleDateString('fr-FR')
      },
      format_percentage: (v) => `${Number(v).toFixed(1)}%`,
      uppercase: (v) => String(v).toUpperCase(),
      lowercase: (v) => String(v).toLowerCase(),
    }
  }

  /**
   * Resout une valeur depuis le source path
   */
  resolve(source: string): string | null {
    if (!source) return null

    const [path, formatterName] = source.split('|')
    const value = this.resolvePath(path.trim())

    if (value === null || value === undefined) return null

    if (formatterName && this.formatters[formatterName.trim()]) {
      return this.formatters[formatterName.trim()](value)
    }

    return String(value)
  }

  private resolvePath(path: string): unknown {
    const parts = path.split('.')

    const roots: Record<string, unknown> = {
      entreprise: this.data.entreprise,
      user: this.data.user,
      scores: {
        latest: this.getLatestScore(),
        all: this.data.scores,
      },
      documents: this.data.documents,
    }

    let current: unknown = roots
    for (const part of parts) {
      if (current === null || current === undefined) return null
      if (typeof current !== 'object') return null

      if (part === 'latest' && Array.isArray(current)) {
        current = current[0] || null
      } else {
        current = (current as Record<string, unknown>)[part]
      }
    }

    return current
  }

  private getLatestScore(): ESGScore | null {
    if (!this.data.scores || this.data.scores.length === 0) return null
    return [...this.data.scores].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0]
  }

  /**
   * Genere un mapping complet pour une etape
   * Retourne { selector: value } pour tous les champs auto-remplissables
   */
  mapStep(fields: Array<{ selector: string; source: string | null }>): Record<string, string> {
    const mapping: Record<string, string> = {}

    for (const field of fields) {
      if (!field.source) continue
      const value = this.resolve(field.source)
      if (value) {
        mapping[field.selector] = value
      }
    }

    return mapping
  }
}
