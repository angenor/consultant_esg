import type { FundField, FundStep } from '@shared/types'

class FieldHighlighter {
  private highlights: Map<string, HTMLElement> = new Map()
  private tooltips: Map<string, HTMLElement> = new Map()

  /**
   * Surligne les champs d'une etape donnee
   */
  highlightStep(step: FundStep, companyData: Record<string, unknown>) {
    this.clearHighlights()

    for (const field of step.fields) {
      const element = this.findElement(field.selector)
      if (!element) continue

      const hasAutoValue = field.source && this.resolveValue(field.source, companyData)
      const highlightType = hasAutoValue ? 'auto' : field.ai_suggest ? 'ai' : 'manual'

      this.addHighlight(element, field, highlightType)
    }
  }

  /**
   * Trouve un element par selecteur CSS (essaie plusieurs selecteurs)
   */
  private findElement(selector: string): HTMLElement | null {
    const selectors = selector.split(',').map(s => s.trim())
    for (const sel of selectors) {
      try {
        const el = document.querySelector<HTMLElement>(sel)
        if (el) return el
      } catch {
        // Selecteur invalide, continuer
      }
    }
    return null
  }

  /**
   * Ajoute un surlignage et un tooltip a un element
   */
  private addHighlight(
    element: HTMLElement,
    field: FundField,
    type: 'auto' | 'ai' | 'manual'
  ) {
    const colors = {
      auto: { border: '#059669', bg: '#f0fdf4', label: 'Auto-remplissage', icon: 'check' },
      ai: { border: '#2563eb', bg: '#eff6ff', label: 'Suggestion IA', icon: 'sparkle' },
      manual: { border: '#d97706', bg: '#fffbeb', label: 'A remplir', icon: 'edit' },
    }
    const config = colors[type]

    // Creer le wrapper de surlignage
    const wrapper = document.createElement('div')
    wrapper.className = 'esg-field-highlight'
    wrapper.style.cssText = `
      position: relative;
      outline: 2px solid ${config.border};
      outline-offset: 2px;
      border-radius: 4px;
      transition: outline-color 0.2s;
    `

    // Badge indicateur
    const badge = document.createElement('div')
    badge.style.cssText = `
      position: absolute;
      top: -10px;
      right: -10px;
      background: ${config.border};
      color: white;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: -apple-system, sans-serif;
      z-index: 999999;
      pointer-events: none;
      white-space: nowrap;
    `
    badge.textContent = config.label

    // Tooltip avec aide
    const tooltip = this.createTooltip(field, type)

    // Wrapper autour de l'element
    element.style.position = 'relative'
    element.parentElement?.insertBefore(wrapper, element)
    wrapper.appendChild(element)
    wrapper.appendChild(badge)

    // Afficher tooltip au hover
    wrapper.addEventListener('mouseenter', () => {
      document.body.appendChild(tooltip)
      const rect = wrapper.getBoundingClientRect()
      tooltip.style.top = `${rect.bottom + window.scrollY + 8}px`
      tooltip.style.left = `${rect.left + window.scrollX}px`
    })

    wrapper.addEventListener('mouseleave', () => {
      tooltip.remove()
    })

    this.highlights.set(field.selector, wrapper)
    this.tooltips.set(field.selector, tooltip)
  }

  /**
   * Cree un tooltip d'aide pour un champ
   */
  private createTooltip(field: FundField, type: 'auto' | 'ai' | 'manual'): HTMLElement {
    const host = document.createElement('div')
    host.style.cssText = `
      position: absolute;
      z-index: 2147483647;
    `

    const shadow = host.attachShadow({ mode: 'closed' })
    shadow.innerHTML = `
      <style>
        .tooltip {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 12px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          max-width: 300px;
          font-family: -apple-system, sans-serif;
          font-size: 13px;
        }
        .tooltip-header {
          font-weight: 600;
          color: #1f2937;
          margin-bottom: 4px;
        }
        .tooltip-help {
          color: #6b7280;
          line-height: 1.4;
        }
        .tooltip-action {
          margin-top: 8px;
          display: flex;
          gap: 8px;
        }
        .tooltip-btn {
          padding: 4px 12px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          border: none;
          transition: background 0.2s;
        }
        .btn-primary {
          background: #059669;
          color: white;
        }
        .btn-primary:hover { background: #047857; }
        .btn-secondary {
          background: #f3f4f6;
          color: #374151;
        }
        .btn-secondary:hover { background: #e5e7eb; }
      </style>
      <div class="tooltip">
        <div class="tooltip-header">${field.label}</div>
        <div class="tooltip-help">${field.help_text}</div>
        <div class="tooltip-action">
          ${type === 'auto' ? '<button class="tooltip-btn btn-primary" data-action="autofill">Remplir automatiquement</button>' : ''}
          ${type === 'ai' ? '<button class="tooltip-btn btn-primary" data-action="ai-suggest">Generer avec l\'IA</button>' : ''}
          <button class="tooltip-btn btn-secondary" data-action="copy">Copier la suggestion</button>
        </div>
      </div>
    `

    return host
  }

  /**
   * Resout une valeur depuis les donnees de l'entreprise
   */
  private resolveValue(path: string, data: Record<string, unknown>): unknown {
    return path.split('.').reduce((obj: unknown, key) => {
      if (obj && typeof obj === 'object') {
        return (obj as Record<string, unknown>)[key]
      }
      return undefined
    }, data)
  }

  /**
   * Supprime tous les surlignages
   */
  clearHighlights() {
    for (const [, wrapper] of this.highlights) {
      const child = wrapper.firstElementChild as HTMLElement
      if (child) {
        wrapper.parentElement?.insertBefore(child, wrapper)
      }
      wrapper.remove()
    }
    for (const [, tooltip] of this.tooltips) {
      tooltip.remove()
    }
    this.highlights.clear()
    this.tooltips.clear()
  }
}

export const fieldHighlighter = new FieldHighlighter()
