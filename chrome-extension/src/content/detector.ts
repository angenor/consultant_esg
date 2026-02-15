import type { FundSiteConfig, ExtensionMessage } from '@shared/types'

class FundDetector {
  private configs: FundSiteConfig[] = []
  private currentConfig: FundSiteConfig | null = null
  private isInitialized = false

  async init() {
    if (this.isInitialized) return
    this.isInitialized = true

    // Charger les configs depuis le service worker
    const response = await chrome.runtime.sendMessage({
      type: 'SYNC_DATA',
    } as ExtensionMessage)

    if (!response) return

    // Charger les configs de fonds
    const configResponse = await chrome.runtime.sendMessage({
      type: 'GET_FUND_CONFIGS',
    } as ExtensionMessage)

    if (configResponse?.configs) {
      this.configs = configResponse.configs
    }

    // Verifier l'URL actuelle
    this.checkCurrentUrl()

    // Observer les changements d'URL (SPA)
    this.observeUrlChanges()
  }

  /**
   * Verifie si l'URL actuelle correspond a un site de fonds
   */
  private checkCurrentUrl() {
    const url = window.location.href

    for (const config of this.configs) {
      const match = config.url_patterns.some(pattern => this.matchUrl(url, pattern))
      if (match) {
        this.onFundDetected(config)
        return
      }
    }

    // Pas de match : nettoyer si necessaire
    if (this.currentConfig) {
      this.onFundLeft()
    }
  }

  /**
   * Detecte les changements d'URL dans les SPA
   */
  private observeUrlChanges() {
    let lastUrl = window.location.href

    // Observer les changements via pushState/replaceState
    const originalPushState = history.pushState
    const originalReplaceState = history.replaceState

    history.pushState = (...args) => {
      originalPushState.apply(history, args)
      this.onUrlChange()
    }

    history.replaceState = (...args) => {
      originalReplaceState.apply(history, args)
      this.onUrlChange()
    }

    window.addEventListener('popstate', () => this.onUrlChange())

    // Fallback : verifier periodiquement
    setInterval(() => {
      if (window.location.href !== lastUrl) {
        lastUrl = window.location.href
        this.onUrlChange()
      }
    }, 1000)
  }

  private onUrlChange() {
    this.checkCurrentUrl()
  }

  /**
   * Quand un site de fonds est detecte
   */
  private async onFundDetected(config: FundSiteConfig) {
    this.currentConfig = config
    console.log(`[ESG Advisor] Fonds detecte : ${config.fonds_nom}`)

    // Notifier le service worker
    await chrome.runtime.sendMessage({
      type: 'FUND_DETECTED',
      payload: {
        url: window.location.href,
        tabId: undefined, // Le SW le recevra via sender.tab.id
        config,
      },
    } as ExtensionMessage)

    // Injecter l'indicateur visuel sur la page
    this.injectDetectionBanner(config)
  }

  /**
   * Quand on quitte un site de fonds
   */
  private onFundLeft() {
    this.currentConfig = null
    this.removeDetectionBanner()
  }

  /**
   * Injecte une banniere discrete en haut de la page via Shadow DOM
   */
  private injectDetectionBanner(config: FundSiteConfig) {
    // Supprimer l'ancienne si existante
    this.removeDetectionBanner()

    // Creer dans un Shadow DOM pour l'isolation CSS
    const host = document.createElement('div')
    host.id = 'esg-advisor-banner-host'
    host.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 2147483647;
      pointer-events: none;
    `

    const shadow = host.attachShadow({ mode: 'closed' })

    const banner = document.createElement('div')
    banner.innerHTML = `
      <style>
        .esg-banner {
          background: linear-gradient(135deg, #059669, #0d9488);
          color: white;
          padding: 8px 16px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 12px;
          pointer-events: auto;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
          animation: slideDown 0.3s ease-out;
        }
        @keyframes slideDown {
          from { transform: translateY(-100%); }
          to { transform: translateY(0); }
        }
        .esg-banner-icon {
          width: 24px;
          height: 24px;
          background: rgba(255,255,255,0.2);
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .esg-banner-text { flex: 1; }
        .esg-banner-text strong { font-weight: 600; }
        .esg-banner-btn {
          background: white;
          color: #059669;
          border: none;
          padding: 6px 16px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
        }
        .esg-banner-btn:hover { background: #f0fdf4; }
        .esg-banner-close {
          background: none;
          border: none;
          color: rgba(255,255,255,0.7);
          cursor: pointer;
          padding: 4px;
          font-size: 18px;
          line-height: 1;
        }
        .esg-banner-close:hover { color: white; }
      </style>
      <div class="esg-banner">
        <div class="esg-banner-icon">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955
                  11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29
                  9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div class="esg-banner-text">
          <strong>${config.fonds_nom}</strong> detecte — ESG Advisor peut vous guider
        </div>
        <button class="esg-banner-btn" id="esg-open-guide">
          Ouvrir le guide
        </button>
        <button class="esg-banner-close" id="esg-close-banner">&#x2715;</button>
      </div>
    `

    shadow.appendChild(banner)
    document.body.appendChild(host)

    // Event listeners
    shadow.getElementById('esg-open-guide')?.addEventListener('click', () => {
      chrome.runtime.sendMessage({ type: 'OPEN_SIDEPANEL' })
    })

    shadow.getElementById('esg-close-banner')?.addEventListener('click', () => {
      host.remove()
    })

    // Auto-hide apres 10 secondes
    setTimeout(() => {
      if (host.parentElement) {
        host.style.transition = 'opacity 0.3s'
        host.style.opacity = '0'
        setTimeout(() => host.remove(), 300)
      }
    }, 10000)
  }

  private removeDetectionBanner() {
    document.getElementById('esg-advisor-banner-host')?.remove()
  }

  /**
   * Match une URL contre un pattern glob
   */
  private matchUrl(url: string, pattern: string): boolean {
    const regex = new RegExp(
      '^' + pattern
        .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
        .replace(/\*/g, '.*')
      + '$'
    )
    return regex.test(url)
  }
}

// Demarrer la detection
const detector = new FundDetector()
detector.init()
