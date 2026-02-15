# Phase 4 : Synchronisation plateforme-extension

## Objectif

Etablir une communication bidirectionnelle temps reel entre la plateforme web (Vue 3) et l'extension Chrome. La plateforme peut envoyer des commandes a l'extension (ouvrir un site, demarrer le guide, pre-remplir un formulaire) et l'extension peut notifier la plateforme de sa progression.

## Architecture de communication

### Contraintes techniques
- L'extension Chrome et la plateforme web sont dans des contextes d'execution differents
- L'extension ne peut PAS ecouter les WebSocket du backend directement depuis le service worker (limitation Manifest V3)
- La communication doit passer par le **content script** injecte sur la page de la plateforme

### Solution : Communication hybride

```
Plateforme (Vue 3)                  Extension Chrome
   |                                    |
   |-- window.postMessage() ---------->|-- content script (ecoute)
   |                                    |      |
   |                                    |      +-- chrome.runtime.sendMessage()
   |                                    |              |
   |                                    |              v
   |                                    |      service worker (traite)
   |                                    |              |
   |                                    |              +-- Execute action
   |                                    |              |   (ouvre onglet, guide, etc.)
   |                                    |              |
   |                                    |              +-- Retourne resultat
   |                                    |              |
   |                                    +-- content script (repond)
   |<-- window.postMessage() ----------|
   |                                    |
   |-- SSE (backend) ----------------->|-- Polling ou events
   |   (notifications, updates)         |   (via API backend)
```

### Canal 1 : Plateforme -> Extension (via postMessage)

La page de la plateforme (`localhost:5173`) envoie des messages via `window.postMessage`.
Le content script de l'extension, injecte sur la plateforme, ecoute ces messages.

### Canal 2 : Extension -> Plateforme (via postMessage retour)

Le content script de l'extension repond via `window.postMessage` sur la meme page.
La plateforme ecoute les messages de type `ESG_EXTENSION_*`.

### Canal 3 : Backend -> Plateforme (SSE existant)

Le backend envoie des evenements SSE pour les notifications et mises a jour.
Deja utilise pour le streaming du chat.

### Canal 4 : Extension -> Backend (API REST)

L'extension appelle les endpoints `/api/extension/*` pour sauvegarder la progression.
Deja implemente.

## Implementation

### Etape 1 : Content script sur la plateforme

**Fichier :** `chrome-extension/src/content/platform-bridge.ts` (nouveau)

Le content script doit etre injecte sur la page de la plateforme (`localhost:5173` ou le domaine de production).

```typescript
// Ecouter les messages de la plateforme
window.addEventListener('message', async (event) => {
  // Verifier l'origine
  if (event.origin !== 'http://localhost:5173' && event.origin !== 'https://app.esg-advisor.com') return

  const { type, payload } = event.data
  if (!type?.startsWith('ESG_PLATFORM_')) return

  switch (type) {
    case 'ESG_PLATFORM_OPEN_FUND_SITE': {
      // Ouvrir le site du fonds dans un nouvel onglet + activer le side panel
      const result = await chrome.runtime.sendMessage({
        type: 'OPEN_FUND_APPLICATION',
        url: payload.url,
        fonds_id: payload.fonds_id,
        intermediaire_id: payload.intermediaire_id,
        application_data: payload.application_data
      })
      // Repondre a la plateforme
      window.postMessage({
        type: 'ESG_EXTENSION_FUND_OPENED',
        payload: result
      }, event.origin)
      break
    }

    case 'ESG_PLATFORM_CHECK_EXTENSION': {
      // Verifier que l'extension est installee et active
      window.postMessage({
        type: 'ESG_EXTENSION_STATUS',
        payload: {
          installed: true,
          version: chrome.runtime.getManifest().version,
          authenticated: await checkAuth()
        }
      }, event.origin)
      break
    }

    case 'ESG_PLATFORM_GET_PROGRESS': {
      // Recuperer la progression d'une candidature
      const progress = await chrome.runtime.sendMessage({
        type: 'GET_APPLICATION_PROGRESS',
        application_id: payload.application_id
      })
      window.postMessage({
        type: 'ESG_EXTENSION_PROGRESS',
        payload: progress
      }, event.origin)
      break
    }

    case 'ESG_PLATFORM_SYNC_DATA': {
      // Forcer une synchronisation des donnees
      await chrome.runtime.sendMessage({ type: 'SYNC_DATA' })
      window.postMessage({
        type: 'ESG_EXTENSION_SYNCED',
        payload: { success: true }
      }, event.origin)
      break
    }
  }
})

// Annoncer la presence de l'extension
window.postMessage({
  type: 'ESG_EXTENSION_READY',
  payload: { version: chrome.runtime.getManifest().version }
}, '*')
```

**Mise a jour du manifest :**

```json
// manifest.json - ajouter la plateforme aux content_scripts
{
  "content_scripts": [
    {
      "matches": ["http://localhost:5173/*", "https://app.esg-advisor.com/*"],
      "js": ["content/platform-bridge.js"],
      "run_at": "document_end"
    },
    {
      "matches": ["<all_urls>"],
      "js": ["content/detector.js"],
      "run_at": "document_idle"
    }
  ]
}
```

### Etape 2 : Composable Vue pour la communication

**Fichier :** `frontend/src/composables/useExtension.ts` (nouveau)

```typescript
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
    authenticated: false
  })
  const pendingRequests = new Map<string, {
    resolve: (value: any) => void
    reject: (error: any) => void
  }>()

  function handleMessage(event: MessageEvent) {
    if (!event.data?.type?.startsWith('ESG_EXTENSION_')) return

    switch (event.data.type) {
      case 'ESG_EXTENSION_READY':
        extensionStatus.value = {
          installed: true,
          version: event.data.payload.version,
          authenticated: false
        }
        // Verifier l'auth de l'extension
        checkExtension()
        break

      case 'ESG_EXTENSION_STATUS':
        extensionStatus.value = {
          installed: true,
          version: event.data.payload.version,
          authenticated: event.data.payload.authenticated
        }
        break

      case 'ESG_EXTENSION_FUND_OPENED':
      case 'ESG_EXTENSION_PROGRESS':
      case 'ESG_EXTENSION_SYNCED':
        // Resoudre les promesses en attente
        const requestId = event.data.payload?._requestId
        if (requestId && pendingRequests.has(requestId)) {
          pendingRequests.get(requestId)!.resolve(event.data.payload)
          pendingRequests.delete(requestId)
        }
        break
    }
  }

  function sendToExtension(type: string, payload: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const requestId = crypto.randomUUID()
      pendingRequests.set(requestId, { resolve, reject })
      window.postMessage({
        type: `ESG_PLATFORM_${type}`,
        payload: { ...payload, _requestId: requestId }
      }, window.location.origin)

      // Timeout apres 10 secondes
      setTimeout(() => {
        if (pendingRequests.has(requestId)) {
          pendingRequests.delete(requestId)
          reject(new Error('Extension timeout'))
        }
      }, 10000)
    })
  }

  function checkExtension() {
    window.postMessage({
      type: 'ESG_PLATFORM_CHECK_EXTENSION',
      payload: {}
    }, window.location.origin)
  }

  async function openFundSite(url: string, fondsId: string, intermediaireId?: string) {
    if (!extensionStatus.value.installed) {
      // Fallback : ouvrir dans un nouvel onglet sans extension
      window.open(url, '_blank')
      return { opened: true, extension: false }
    }
    return sendToExtension('OPEN_FUND_SITE', {
      url,
      fonds_id: fondsId,
      intermediaire_id: intermediaireId
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
    // Verifier si l'extension est presente
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
    checkExtension
  }
}
```

### Etape 3 : Nouveaux message types dans le service worker

**Fichier :** `chrome-extension/src/background/service-worker.ts`

Ajouter les handlers pour les nouveaux types de messages :

```typescript
case 'OPEN_FUND_APPLICATION': {
  // 1. Creer un nouvel onglet avec l'URL du formulaire
  const tab = await chrome.tabs.create({ url: message.url })

  // 2. Sauvegarder le contexte pour le side panel
  await chrome.storage.session.set({
    pending_fund_application: {
      fonds_id: message.fonds_id,
      intermediaire_id: message.intermediaire_id,
      tab_id: tab.id,
      application_data: message.application_data
    }
  })

  // 3. Ouvrir le side panel sur le nouvel onglet
  if (tab.id) {
    await chrome.sidePanel.open({ tabId: tab.id })
  }

  return { opened: true, tab_id: tab.id }
}

case 'GET_APPLICATION_PROGRESS': {
  // Recuperer la progression depuis le backend
  const app = await apiClient.get(`/extension/applications/${message.application_id}`)
  return app
}
```

### Etape 4 : Integration dans le chat

**Fichier :** `frontend/src/components/chat/ChatMessage.vue`

Quand le LLM retourne une `extension_action` dans le resultat d'un skill :

```vue
<script setup>
import { useExtension } from '../../composables/useExtension'

const { extensionStatus, openFundSite } = useExtension()

async function handleExtensionAction(action: any) {
  if (action.type === 'OPEN_FUND_APPLICATION') {
    try {
      await openFundSite(action.url, action.fonds_id, action.intermediaire_id)
    } catch (e) {
      // Fallback : lien simple
      window.open(action.url, '_blank')
    }
  }
}
</script>

<template>
  <!-- Dans le rendu du message, detecter extension_action -->
  <div v-if="skillResult?.extension_action" class="extension-action-card">
    <p>{{ skillResult.instructions }}</p>

    <div v-if="extensionStatus.installed" class="flex gap-2 mt-3">
      <button @click="handleExtensionAction(skillResult.extension_action)"
              class="bg-emerald-600 text-white px-4 py-2 rounded-lg">
        Ouvrir avec l'extension Chrome
      </button>
    </div>

    <div v-else class="mt-3 p-3 bg-amber-50 rounded-lg text-sm">
      <p>L'extension Chrome ESG Mefali n'est pas detectee.</p>
      <a :href="skillResult.extension_action.url" target="_blank"
         class="text-emerald-600 underline">
        Ouvrir le site dans un nouvel onglet
      </a>
    </div>
  </div>
</template>
```

### Etape 5 : Notifications temps reel (Backend -> Frontend)

**Fichier :** `backend/app/api/notifications.py` (nouveau ou extension)

Endpoint SSE pour les notifications en temps reel :

```python
@router.get("/api/notifications/stream")
async def notification_stream(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    async def event_generator():
        while True:
            # Verifier les nouvelles notifications
            notifs = await get_unread_notifications(db, current_user.id)
            for n in notifs:
                yield {
                    "event": "notification",
                    "data": json.dumps({
                        "id": str(n.id),
                        "type": n.type,
                        "titre": n.titre,
                        "contenu": n.contenu,
                        "data": n.data_json,
                        "created_at": n.created_at.isoformat()
                    })
                }
                await mark_as_read(db, n.id)
            await asyncio.sleep(5)  # Poll toutes les 5 secondes

    return EventSourceResponse(event_generator())
```

**Types de notifications pertinents :**
- `candidature_progress` : progression de candidature mise a jour depuis l'extension
- `dossier_genere` : dossier de candidature pret au telechargement
- `extension_sync` : donnees synchronisees avec l'extension
- `deadline_approaching` : date limite de fonds approche

### Etape 6 : Endpoint de callback extension -> backend -> plateforme

**Fichier :** `backend/app/api/extension.py`

Ajouter un endpoint pour que l'extension signale les evenements importants :

```python
@router.post("/api/extension/events")
async def extension_event(
    event: ExtensionEventRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Recoit les evenements de l'extension (formulaire soumis, etape completee, etc.)"""

    if event.type == "step_completed":
        # Mettre a jour la candidature
        await update_application_progress(db, event.application_id, event.step, event.progress_pct)
        # Creer notification pour la plateforme
        await create_notification(db, current_user.id, ...)

    elif event.type == "form_submitted":
        # Marquer la candidature comme soumise
        await mark_application_submitted(db, event.application_id)
        await create_notification(db, current_user.id, ...)

    elif event.type == "error":
        # Logger l'erreur
        logger.error(f"Extension error: {event.details}")

    return {"status": "ok"}
```

## Protocole de messages

### Plateforme -> Extension

| Type | Payload | Action |
|------|---------|--------|
| `ESG_PLATFORM_CHECK_EXTENSION` | `{}` | Verifier presence extension |
| `ESG_PLATFORM_OPEN_FUND_SITE` | `{url, fonds_id, intermediaire_id}` | Ouvrir site + side panel |
| `ESG_PLATFORM_GET_PROGRESS` | `{application_id}` | Recuperer progression |
| `ESG_PLATFORM_SYNC_DATA` | `{}` | Forcer synchronisation |

### Extension -> Plateforme

| Type | Payload | Quand |
|------|---------|-------|
| `ESG_EXTENSION_READY` | `{version}` | Au chargement de la page plateforme |
| `ESG_EXTENSION_STATUS` | `{installed, version, authenticated}` | Reponse a CHECK |
| `ESG_EXTENSION_FUND_OPENED` | `{opened, tab_id}` | Site ouvert avec succes |
| `ESG_EXTENSION_PROGRESS` | `{application_id, step, progress_pct}` | Progression mise a jour |
| `ESG_EXTENSION_SYNCED` | `{success}` | Synchronisation terminee |

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `chrome-extension/src/content/platform-bridge.ts` | Content script pont |
| `frontend/src/composables/useExtension.ts` | Composable communication |

## Fichiers a modifier

| Fichier | Modification |
|---------|--------------|
| `chrome-extension/manifest.json` | Ajouter content_script pour la plateforme |
| `chrome-extension/src/background/service-worker.ts` | Ajouter handlers OPEN_FUND_APPLICATION |
| `chrome-extension/src/shared/types.ts` | Ajouter nouveaux message types |
| `chrome-extension/vite.config.ts` | Ajouter build entry pour platform-bridge |
| `backend/app/api/extension.py` | Ajouter endpoint events |
| `frontend/src/components/chat/ChatMessage.vue` | Integration extension actions |
| `backend/app/api/notifications.py` | SSE endpoint (si pas existant) |

## Securite

- **Verification d'origine** : `postMessage` verifie `event.origin` (localhost:5173 ou domaine prod)
- **Pas de donnees sensibles** dans les messages postMessage (pas de JWT, pas de mots de passe)
- **L'extension authentifie separement** via son propre JWT dans chrome.storage.session
- **Rate limiting** sur l'endpoint `/api/extension/events`

## Fallbacks

1. **Extension non installee** : la plateforme detecte l'absence via timeout sur `CHECK_EXTENSION` et propose un lien direct
2. **Extension non authentifiee** : message d'avertissement invitant a se connecter dans l'extension
3. **Communication echouee** : timeout de 10s + fallback vers ouverture classique dans nouvel onglet

## Criteres de validation

- [ ] Content script `platform-bridge.ts` injecte sur la page de la plateforme
- [ ] `useExtension()` composable detecte l'extension installee
- [ ] `openFundSite()` ouvre un onglet et active le side panel
- [ ] Fallback fonctionne quand l'extension n'est pas installee
- [ ] L'extension peut signaler la progression au backend
- [ ] Le backend cree des notifications lors d'evenements extension
- [ ] Pas de fuite de donnees sensibles via postMessage
