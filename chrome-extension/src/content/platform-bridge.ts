/**
 * Content script pont plateforme <-> extension.
 * Injecté uniquement sur la plateforme (localhost:5173 / app.esg-advisor.com).
 * Relaie les messages window.postMessage vers le service worker via chrome.runtime.sendMessage.
 */

const ALLOWED_ORIGINS = [
  'http://localhost:5173',
  'https://app.esg-advisor.com',
]

async function checkAuth(): Promise<boolean> {
  try {
    const result = await chrome.runtime.sendMessage({ type: 'AUTH_STATUS' })
    return result?.authenticated ?? false
  } catch {
    return false
  }
}

window.addEventListener('message', async (event) => {
  if (!ALLOWED_ORIGINS.includes(event.origin)) return

  const { type, payload } = event.data || {}
  if (!type?.startsWith('ESG_PLATFORM_')) return

  switch (type) {
    case 'ESG_PLATFORM_CHECK_EXTENSION': {
      const authenticated = await checkAuth()
      window.postMessage({
        type: 'ESG_EXTENSION_STATUS',
        payload: {
          installed: true,
          version: chrome.runtime.getManifest().version,
          authenticated,
        },
      }, event.origin)
      break
    }

    case 'ESG_PLATFORM_OPEN_FUND_SITE': {
      try {
        const result = await chrome.runtime.sendMessage({
          type: 'OPEN_FUND_APPLICATION',
          payload: {
            url: payload.url,
            fonds_id: payload.fonds_id,
            intermediaire_id: payload.intermediaire_id,
            application_data: payload.application_data,
          },
        })
        window.postMessage({
          type: 'ESG_EXTENSION_FUND_OPENED',
          payload: { ...result, _requestId: payload._requestId },
        }, event.origin)
      } catch (error) {
        window.postMessage({
          type: 'ESG_EXTENSION_FUND_OPENED',
          payload: {
            opened: false,
            error: String(error),
            _requestId: payload._requestId,
          },
        }, event.origin)
      }
      break
    }

    case 'ESG_PLATFORM_GET_PROGRESS': {
      try {
        const result = await chrome.runtime.sendMessage({
          type: 'GET_APPLICATION_PROGRESS',
          payload: { application_id: payload.application_id },
        })
        window.postMessage({
          type: 'ESG_EXTENSION_PROGRESS',
          payload: { ...result, _requestId: payload._requestId },
        }, event.origin)
      } catch (error) {
        window.postMessage({
          type: 'ESG_EXTENSION_PROGRESS',
          payload: {
            error: String(error),
            _requestId: payload._requestId,
          },
        }, event.origin)
      }
      break
    }

    case 'ESG_PLATFORM_SYNC_DATA': {
      try {
        await chrome.runtime.sendMessage({ type: 'SYNC_DATA' })
        window.postMessage({
          type: 'ESG_EXTENSION_SYNCED',
          payload: { success: true, _requestId: payload?._requestId },
        }, event.origin)
      } catch (error) {
        window.postMessage({
          type: 'ESG_EXTENSION_SYNCED',
          payload: {
            success: false,
            error: String(error),
            _requestId: payload?._requestId,
          },
        }, event.origin)
      }
      break
    }
  }
})

// Annoncer la présence de l'extension au chargement
window.postMessage({
  type: 'ESG_EXTENSION_READY',
  payload: { version: chrome.runtime.getManifest().version },
}, '*')
