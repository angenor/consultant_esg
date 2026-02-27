import { ref, onMounted, onUnmounted } from 'vue'

interface ExtensionStatus {
  installed: boolean
  version: string | null
  authenticated: boolean
}

export function useExtension() {
  const extensionStatus = ref<ExtensionStatus>({
    installed: false,
    version: null,
    authenticated: false,
  })

  const pendingRequests = new Map<
    string,
    { resolve: (value: unknown) => void; reject: (error: Error) => void }
  >()

  function handleMessage(event: MessageEvent) {
    if (!event.data?.type?.startsWith('ESG_EXTENSION_')) return

    switch (event.data.type) {
      case 'ESG_EXTENSION_READY':
        extensionStatus.value = {
          installed: true,
          version: event.data.payload?.version ?? null,
          authenticated: false,
        }
        checkExtension()
        break

      case 'ESG_EXTENSION_STATUS':
        extensionStatus.value = {
          installed: true,
          version: event.data.payload?.version ?? null,
          authenticated: event.data.payload?.authenticated ?? false,
        }
        break

      case 'ESG_EXTENSION_FUND_OPENED':
      case 'ESG_EXTENSION_PROGRESS':
      case 'ESG_EXTENSION_SYNCED': {
        const requestId = event.data.payload?._requestId
        if (requestId && pendingRequests.has(requestId)) {
          pendingRequests.get(requestId)!.resolve(event.data.payload)
          pendingRequests.delete(requestId)
        }
        break
      }
    }
  }

  function sendToExtension(type: string, payload: Record<string, unknown>): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const requestId = crypto.randomUUID()
      pendingRequests.set(requestId, { resolve, reject })

      window.postMessage(
        {
          type: `ESG_PLATFORM_${type}`,
          payload: { ...payload, _requestId: requestId },
        },
        window.location.origin,
      )

      setTimeout(() => {
        if (pendingRequests.has(requestId)) {
          pendingRequests.delete(requestId)
          reject(new Error('Extension timeout'))
        }
      }, 10000)
    })
  }

  function checkExtension() {
    window.postMessage(
      { type: 'ESG_PLATFORM_CHECK_EXTENSION', payload: {} },
      window.location.origin,
    )
  }

  async function openFundSite(
    url: string,
    fondsId: string,
    intermediaireId?: string,
    applicationData?: Record<string, unknown>,
  ) {
    if (!extensionStatus.value.installed) {
      window.open(url, '_blank')
      return { opened: true, extension: false }
    }
    return sendToExtension('OPEN_FUND_SITE', {
      url,
      fonds_id: fondsId,
      intermediaire_id: intermediaireId,
      application_data: applicationData,
    })
  }

  async function getProgress(applicationId: string) {
    return sendToExtension('GET_PROGRESS', { application_id: applicationId })
  }

  async function syncData() {
    return sendToExtension('SYNC_DATA', {})
  }

  onMounted(() => {
    window.addEventListener('message', handleMessage)
    checkExtension()
  })

  onUnmounted(() => {
    window.removeEventListener('message', handleMessage)
  })

  return {
    extensionStatus,
    openFundSite,
    getProgress,
    syncData,
    checkExtension,
  }
}
