# Phase 2 : Flux candidature depuis recommandation

## Dependances

**Prerequis :** Phase 1 (scoring fiable pour prioriser les recommandations)
**Bloque :** Phase 4 (le flux candidature doit exister avant d'y greffer la checklist)

## Progression

- [x] 2.1 Deduplication des candidatures (empecher les doublons fonds_id + entreprise_id)
- [x] 2.2 Confirmation utilisateur avant creation de candidature
- [x] 2.3 Workflow adapte selon `mode_acces` (direct vs intermediaire)
- [x] 2.4 Lien bidirectionnel popup ↔ side panel (ouvrir le guide apres "Postuler")
- [x] 2.5 Feedback visuel post-creation (toast + mise a jour de la liste)
- [x] 2.6 Tests unitaires du flux candidature

## Objectif

Creer un flux fluide entre le clic "Postuler" sur une recommandation et le demarrage effectif de la candidature dans le side panel, en gerant les cas particuliers (doublon, intermediaire, fonds sans URL).

## Etat actuel (correctif rapide applique)

### Ce qui existe
- Bouton "Postuler" dans `FundRecommendation.vue` qui emet `start-application`
- `DashboardPanel.vue` : `handleStartApplication()` appelle `createApplication()` puis ouvre l'URL
- `applications.ts` : store avec `createApplication()` qui POST vers `/api/extension/applications`
- Side panel : `autoCreateApplication()` cree une candidature quand un fonds est detecte

### Ce qui manque
- **Deduplication** : si l'utilisateur clique 2 fois sur "Postuler", 2 candidatures sont creees
- **Confirmation** : aucune confirmation avant creation — un clic = une candidature
- **Adaptation mode_acces** : "Postuler" sur un fonds a acces `banque_partenaire` ouvre le site du fonds, mais devrait guider vers l'intermediaire
- **Lien popup → side panel** : apres "Postuler", l'utilisateur doit manuellement ouvrir le side panel
- **Feedback** : aucun toast ni animation pour confirmer la creation

## Implementation detaillee

### 2.1 Deduplication des candidatures

**Fichier backend :** `backend/app/api/extension.py` → `create_application()`

```python
# Avant de creer, verifier si une candidature active existe deja
existing = await db.execute(
    select(FundApplication)
    .where(
        FundApplication.entreprise_id == entreprise.id,
        FundApplication.fonds_id == data.fonds_id,
        FundApplication.status.in_(["brouillon", "en_cours"]),
    )
)
if existing.scalar_one_or_none():
    raise HTTPException(409, "Une candidature est deja en cours pour ce fonds")
```

**Fichier extension :** `chrome-extension/src/shared/stores/applications.ts`

Gerer le code 409 dans `createApplication()` et retourner la candidature existante :
```typescript
if (error.status === 409) {
  // Retrouver la candidature existante
  const existing = applications.value.find(
    a => a.fonds_id === data.fonds_id && ['brouillon', 'en_cours'].includes(a.status)
  )
  return existing || null
}
```

### 2.2 Confirmation utilisateur

**Fichier :** `chrome-extension/src/popup/components/DashboardPanel.vue`

Ajouter un dialogue de confirmation avant creation :
```vue
<!-- Modal confirmation -->
<div v-if="pendingFonds" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
  <div class="bg-white rounded-xl p-4 m-4 max-w-sm">
    <h3 class="font-semibold text-gray-800">Commencer la candidature ?</h3>
    <p class="text-sm text-gray-500 mt-1">
      {{ pendingFonds.nom }} — {{ pendingFonds.institution }}
    </p>
    <!-- Afficher le mode d'acces si != direct -->
    <div v-if="pendingFonds.mode_acces && pendingFonds.mode_acces !== 'direct'"
         class="mt-2 bg-amber-50 rounded-lg p-2 text-xs text-amber-700">
      Ce fonds necessite un intermediaire ({{ modeAccesLabel }}).
    </div>
    <div class="flex gap-2 mt-4">
      <button @click="pendingFonds = null" class="flex-1 btn-secondary">Annuler</button>
      <button @click="confirmApplication" class="flex-1 btn-primary">Postuler</button>
    </div>
  </div>
</div>
```

### 2.3 Workflow adapte selon mode_acces

**Fichier :** `chrome-extension/src/popup/components/DashboardPanel.vue` → `confirmApplication()`

```typescript
async function confirmApplication() {
  if (!pendingFonds.value) return

  const fonds = pendingFonds.value
  const app = await createApplication({
    fonds_id: fonds.id,
    fonds_nom: fonds.nom,
    fonds_institution: fonds.institution || '',
    url_candidature: fonds.url_source || undefined,
  })

  pendingFonds.value = null
  emit('refresh')

  switch (fonds.mode_acces) {
    case 'direct':
    case 'appel_propositions':
      // Ouvrir le site du fonds et le side panel
      if (fonds.url_source) {
        chrome.tabs.create({ url: fonds.url_source })
      }
      // Ouvrir automatiquement le side panel
      chrome.runtime.sendMessage({ type: 'OPEN_SIDEPANEL' })
      break

    case 'banque_partenaire':
    case 'entite_accreditee':
    case 'banque_multilaterale':
      // Ouvrir la page de l'intermediaire (si connue)
      const intermediaire_url = fonds.acces_details?.intermediaire_url
      if (intermediaire_url) {
        chrome.tabs.create({ url: intermediaire_url })
      }
      // Notification avec instructions
      showToast(`Contactez l'intermediaire pour ${fonds.nom}`)
      break

    case 'garantie_bancaire':
      // Guide specifique
      showToast('Consultez votre banque pour la garantie')
      break
  }
}
```

### 2.4 Lien popup → side panel

**Fichier :** `chrome-extension/src/background/service-worker.ts`

Ajouter un handler pour ouvrir le side panel apres creation de candidature :
```typescript
// Handler OPEN_FUND_APPLICATION
case 'OPEN_FUND_APPLICATION': {
  const { config, applicationId } = message.payload
  // Ouvrir le side panel avec le contexte
  await chrome.sidePanel.open({ windowId: sender.tab?.windowId })
  // Transmettre la config au side panel
  chrome.runtime.sendMessage({
    type: 'FUND_DETECTED',
    payload: { config, applicationId },
  })
  break
}
```

**Fichier :** `chrome-extension/src/sidepanel/App.vue`

Modifier `onMounted` pour accepter un `applicationId` et le reutiliser au lieu de recreer :
```typescript
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'FUND_DETECTED' && message.payload?.config) {
    fundConfig.value = message.payload.config
    currentStep.value = 0
    // Reutiliser l'application existante si fournie
    if (message.payload.applicationId) {
      activeApplicationId.value = message.payload.applicationId
    } else {
      autoCreateApplication(message.payload.config)
    }
  }
})
```

### 2.5 Feedback visuel (toast)

**Fichier a creer :** `chrome-extension/src/popup/components/Toast.vue`

Composant toast reutilisable avec auto-dismiss :
```vue
<template>
  <Transition name="toast">
    <div v-if="visible" class="fixed bottom-4 left-4 right-4 z-50">
      <div class="bg-gray-800 text-white rounded-lg px-4 py-3 text-sm shadow-lg
                  flex items-center gap-2">
        <svg v-if="type === 'success'" class="w-4 h-4 text-emerald-400">...</svg>
        <svg v-else class="w-4 h-4 text-amber-400">...</svg>
        <span>{{ message }}</span>
      </div>
    </div>
  </Transition>
</template>
```

**Fichier :** `chrome-extension/src/popup/components/DashboardPanel.vue`

Ajouter le toast et le declencher apres creation reussie :
```typescript
const toastMessage = ref('')
const toastVisible = ref(false)

function showToast(msg: string) {
  toastMessage.value = msg
  toastVisible.value = true
  setTimeout(() => { toastVisible.value = false }, 3000)
}
```

### 2.6 Tests unitaires

**Fichier :** `chrome-extension/tests/candidature-flow.test.ts`

```typescript
// Cas a tester :
// - createApplication() avec fonds_id existant → retourne candidature existante (409)
// - createApplication() avec nouveau fonds → cree candidature
// - confirmApplication() mode_acces='direct' → ouvre URL + side panel
// - confirmApplication() mode_acces='banque_partenaire' → ouvre intermediaire
// - handleStartApplication() sans url_source → pas d'ouverture de tab
// - Doublon detection : 2 clics rapides → 1 seule candidature
```

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `chrome-extension/src/popup/components/Toast.vue` | Composant toast reutilisable |
| `chrome-extension/tests/candidature-flow.test.ts` | Tests du flux candidature |

## Fichiers a modifier

| Fichier | Modification |
|---------|-------------|
| `backend/app/api/extension.py` | Deduplication dans `create_application` |
| `chrome-extension/src/shared/stores/applications.ts` | Gestion 409, retour candidature existante |
| `chrome-extension/src/popup/components/DashboardPanel.vue` | Modal confirmation, workflow mode_acces, toast |
| `chrome-extension/src/popup/components/FundRecommendation.vue` | Bouton "Reprendre" si candidature existante |
| `chrome-extension/src/background/service-worker.ts` | Handler OPEN_FUND_APPLICATION |
| `chrome-extension/src/sidepanel/App.vue` | Reutiliser applicationId, pas de doublon |

## Criteres de validation

- [ ] Pas de doublon possible (clic double, clic popup + side panel)
- [ ] Confirmation affichee avant creation
- [ ] Mode d'acces "intermediaire" ouvre la bonne page
- [ ] Le side panel s'ouvre automatiquement apres "Postuler" (mode direct)
- [ ] Toast visible pendant 3 secondes apres creation
- [ ] Tests unitaires passent
