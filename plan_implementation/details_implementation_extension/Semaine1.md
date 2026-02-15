# Semaine 1 : Infrastructure, Authentification & Popup

## Dependances

| Prerequis | Fichier/Ressource | Statut |
|-----------|-------------------|--------|
| Lire le document d'architecture | [00_vision_et_architecture.md](./00_vision_et_architecture.md) | [ ] |
| Backend ESG Advisor fonctionnel | `docker compose up -d` (db + backend) | [ ] |
| Node.js 20+ installe | `node -v` | [ ] |
| Chrome installe (mode developpeur) | `chrome://extensions` | [ ] |

> **Aucun fichier Semaine ne depend de celui-ci en amont.**
> Ce fichier doit etre termine **avant** de commencer [Semaine2.md](./Semaine2.md).

---

## Progression Semaine 1

- [ ] **Etape 1** : Initialisation du projet extension
  - [ ] 1.1 Structure du projet (`mkdir`, `npm init`)
  - [ ] 1.2 Dependencies installees (`npm install`)
  - [ ] 1.3 Manifest V3 cree
  - [ ] 1.4 Configuration Vite fonctionnelle
  - [ ] 1.5 Arborescence initiale creee
  - [ ] **Validation** : `npm run build` produit `dist/`
- [ ] **Etape 2** : Types & constantes partages
  - [ ] 2.1 `src/shared/types.ts` complet
  - [ ] 2.2 `src/shared/constants.ts` complet
  - [ ] **Validation** : Compilation TypeScript sans erreur
- [ ] **Etape 3** : Client API & authentification
  - [ ] 3.1 `src/shared/api-client.ts` (requetes HTTP + JWT)
  - [ ] 3.2 `src/shared/auth.ts` (login, logout, checkAuth)
  - [ ] 3.3 `src/shared/storage.ts` (cache chrome.storage)
  - [ ] **Validation** : Login → token dans `chrome.storage.session`
- [ ] **Etape 4** : Service Worker (background)
  - [ ] 4.1 `src/background/service-worker.ts` (messages, alarmes, sync)
  - [ ] **Validation** : SW demarre, gere les messages, synchronise
- [ ] **Etape 5** : Popup (interface principale)
  - [ ] 5.1 `popup/index.html` + `popup/main.ts`
  - [ ] 5.2 `popup/App.vue` (layout principal)
  - [ ] 5.3 `LoginPanel.vue`
  - [ ] 5.4 `DashboardPanel.vue`
  - [ ] 5.5 `ApplicationCard.vue` + `FundRecommendation.vue`
  - [ ] **Validation** : Popup s'ouvre, login fonctionne, dashboard affiche les donnees
- [ ] **Etape 6** : Nouveaux endpoints backend
  - [ ] 6.1 Modele `FundApplication` + `FundSiteConfig`
  - [ ] 6.2 Migration Alembic executee
  - [ ] 6.3 API `/api/extension/*` (6 endpoints)
  - [ ] 6.4 Routeur enregistre dans `main.py`
  - [ ] **Validation** : Endpoints repondent via `curl`
- [ ] **Etape 7** : Seed des configurations de sites
  - [ ] 7.1 `data/fund_site_configs.json` cree
  - [ ] 7.2 Script de seed execute
  - [ ] **Validation** : `GET /api/extension/fund-configs` retourne les configs

---

## Objectifs de la semaine
- Mettre en place le projet d'extension Chrome (Manifest V3)
- Configurer le build system (Vite + Vue 3 + TailwindCSS)
- Implementer l'authentification avec le backend existant
- Creer le popup avec login et dashboard des candidatures
- Ajouter les nouveaux endpoints backend pour l'extension

---

## Etape 1 : Initialisation du Projet Extension

### 1.1 Structure du projet

```bash
# Depuis la racine du projet
mkdir -p chrome-extension
cd chrome-extension
npm init -y
```

### 1.2 Dependencies

```json
{
  "name": "esg-advisor-chrome-extension",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite build --watch --mode development",
    "build": "vite build --mode production",
    "preview": "vite preview",
    "type-check": "vue-tsc --noEmit"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "pinia": "^3.0.0"
  },
  "devDependencies": {
    "@anthropic-ai/sdk": "^0.30.0",
    "@crxjs/vite-plugin": "^2.0.0-beta.25",
    "@tailwindcss/vite": "^4.1.0",
    "@types/chrome": "^0.0.280",
    "@vitejs/plugin-vue": "^5.0.0",
    "tailwindcss": "^4.1.0",
    "typescript": "^5.9.0",
    "vite": "^7.0.0",
    "vue-tsc": "^2.0.0"
  }
}
```

### 1.3 Manifest V3

```json
// chrome-extension/manifest.json
{
  "manifest_version": 3,
  "name": "ESG Advisor Guide",
  "description": "Guide pas-a-pas pour vos candidatures aux fonds verts africains",
  "version": "1.0.0",
  "default_locale": "fr",

  "icons": {
    "16": "assets/icons/icon-16.png",
    "32": "assets/icons/icon-32.png",
    "48": "assets/icons/icon-48.png",
    "128": "assets/icons/icon-128.png"
  },

  "action": {
    "default_popup": "popup/index.html",
    "default_icon": {
      "16": "assets/icons/icon-16.png",
      "32": "assets/icons/icon-32.png"
    },
    "default_title": "ESG Advisor Guide"
  },

  "side_panel": {
    "default_path": "sidepanel/index.html"
  },

  "background": {
    "service_worker": "background/service-worker.ts",
    "type": "module"
  },

  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content/detector.ts"],
      "run_at": "document_idle"
    }
  ],

  "permissions": [
    "activeTab",
    "storage",
    "sidePanel",
    "notifications",
    "alarms"
  ],

  "host_permissions": [
    "https://api.esgadvisor.ai/*",
    "http://localhost:8000/*"
  ],

  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  },

  "web_accessible_resources": [
    {
      "resources": ["assets/*"],
      "matches": ["<all_urls>"]
    }
  ]
}
```

### 1.4 Configuration Vite

```typescript
// chrome-extension/vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { crx } from '@crxjs/vite-plugin'
import manifest from './manifest.json'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    crx({ manifest }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@shared': resolve(__dirname, 'src/shared'),
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  }
})
```

### 1.5 Arborescence initiale

```
chrome-extension/
├── manifest.json
├── vite.config.ts
├── tsconfig.json
├── package.json
│
├── src/
│   ├── popup/
│   │   ├── index.html
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── LoginPanel.vue
│   │   │   ├── DashboardPanel.vue
│   │   │   ├── ApplicationCard.vue
│   │   │   └── FundRecommendation.vue
│   │   └── stores/
│   │       └── popup.ts
│   │
│   ├── sidepanel/
│   │   ├── index.html
│   │   ├── main.ts
│   │   └── App.vue           (placeholder)
│   │
│   ├── background/
│   │   └── service-worker.ts
│   │
│   ├── content/
│   │   └── detector.ts        (placeholder)
│   │
│   └── shared/
│       ├── types.ts
│       ├── constants.ts
│       ├── api-client.ts
│       ├── auth.ts
│       └── storage.ts
│
└── assets/
    ├── icons/
    │   ├── icon-16.png
    │   ├── icon-32.png
    │   ├── icon-48.png
    │   └── icon-128.png
    └── styles/
        └── main.css
```

**Critere de validation :** `npm run build` produit un dossier `dist/` avec le manifest, le popup et le service worker fonctionnels.

---

## Etape 2 : Types & Constantes Partages

### 2.1 Types TypeScript

```typescript
// src/shared/types.ts

// === Auth ===
export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface User {
  id: string
  email: string
  nom_complet: string
  role: 'user' | 'admin'
  is_active: boolean
}

// === Entreprise ===
export interface Entreprise {
  id: string
  nom: string
  secteur: string | null
  sous_secteur: string | null
  pays: string
  ville: string | null
  effectifs: number | null
  chiffre_affaires: number | null
  devise: string
  description: string | null
  profil_json: Record<string, unknown> | null
}

// === ESG Score ===
export interface ESGScore {
  id: string
  score_e: number | null
  score_s: number | null
  score_g: number | null
  score_global: number | null
  referentiel_code: string
  created_at: string
}

// === Fonds Vert ===
export interface FondsVert {
  id: string
  nom: string
  institution: string | null
  type: 'pret' | 'subvention' | 'garantie'
  montant_min: number | null
  montant_max: number | null
  devise: string
  secteurs_json: string[] | null
  pays_eligibles: string[] | null
  criteres_json: Record<string, unknown> | null
  date_limite: string | null
  url_source: string | null
  is_active: boolean
  compatibility_score?: number  // Calcule cote client
}

// === Candidature (nouveau) ===
export interface FundApplication {
  id: string
  entreprise_id: string
  fonds_id: string | null
  fonds_nom: string
  fonds_institution: string
  status: ApplicationStatus
  progress_pct: number
  form_data: Record<string, unknown>
  current_step: number
  total_steps: number | null
  url_candidature: string | null
  notes: string | null
  started_at: string
  submitted_at: string | null
  updated_at: string | null
}

export type ApplicationStatus =
  | 'brouillon'
  | 'en_cours'
  | 'soumise'
  | 'acceptee'
  | 'refusee'
  | 'abandonnee'

// === Config Site Fonds (nouveau) ===
export interface FundSiteConfig {
  id: string
  fonds_id: string
  fonds_nom: string
  url_patterns: string[]
  steps: FundStep[]
  required_docs: RequiredDoc[]
  tips: Record<string, string> | null
  is_active: boolean
  version: number
}

export interface FundStep {
  order: number
  title: string
  description: string
  url_pattern: string | null
  fields: FundField[]
}

export interface FundField {
  selector: string
  label: string
  source: string | null      // Chemin vers la donnee dans le profil
  help_text: string
  type: 'text' | 'number' | 'select' | 'textarea' | 'file' | 'date'
  required: boolean
  ai_suggest: boolean        // Si true, le LLM peut suggerer le contenu
}

export interface RequiredDoc {
  name: string
  type: string               // "legal", "financial", "esg", "technical"
  format: string             // "PDF", "XLSX", etc.
  description: string
  available_on_platform: boolean  // Calcule a la synchronisation
  document_id: string | null     // ID du document sur la plateforme
}

// === Messages inter-composants ===
export type MessageType =
  | 'AUTH_STATUS'
  | 'FUND_DETECTED'
  | 'OPEN_SIDEPANEL'
  | 'SYNC_DATA'
  | 'SAVE_PROGRESS'
  | 'FIELD_SUGGESTION'
  | 'GET_COMPANY_DATA'

export interface ExtensionMessage {
  type: MessageType
  payload?: unknown
}

// === Donnees synchronisees ===
export interface SyncedData {
  user: User
  entreprise: Entreprise | null
  scores: ESGScore[]
  documents: DocumentSummary[]
  fonds_recommandes: FondsVert[]
  applications: FundApplication[]
  last_synced: string
}

export interface DocumentSummary {
  id: string
  nom_fichier: string
  type_mime: string
  taille: number
  created_at: string
}
```

### 2.2 Constantes

```typescript
// src/shared/constants.ts

// URL de l'API backend (configurable)
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Cles de stockage Chrome
export const STORAGE_KEYS = {
  TOKEN: 'esg_jwt_token',
  USER: 'esg_user',
  SYNCED_DATA: 'esg_synced_data',
  FUND_CONFIGS: 'esg_fund_configs',
  ACTIVE_APPLICATION: 'esg_active_application',
  SETTINGS: 'esg_settings',
} as const

// Durees (en millisecondes)
export const CACHE_TTL = {
  SYNCED_DATA: 5 * 60 * 1000,     // 5 minutes
  FUND_CONFIGS: 60 * 60 * 1000,    // 1 heure
  TOKEN_CHECK: 30 * 60 * 1000,     // 30 minutes
} as const

// Statuts de candidature avec labels et couleurs
export const APPLICATION_STATUSES = {
  brouillon:  { label: 'Brouillon',  color: 'gray',    icon: 'draft' },
  en_cours:   { label: 'En cours',   color: 'blue',    icon: 'progress' },
  soumise:    { label: 'Soumise',    color: 'amber',   icon: 'sent' },
  acceptee:   { label: 'Acceptee',   color: 'emerald', icon: 'check' },
  refusee:    { label: 'Refusee',    color: 'red',     icon: 'cross' },
  abandonnee: { label: 'Abandonnee', color: 'gray',    icon: 'archive' },
} as const

// Couleurs du theme (coherent avec la plateforme)
export const THEME = {
  primary: '#059669',      // emerald-600
  primaryLight: '#10b981', // emerald-500
  secondary: '#0d9488',    // teal-600
  accent: '#d97706',       // amber-600
  error: '#dc2626',        // red-600
  background: '#f9fafb',   // gray-50
} as const
```

**Critere de validation :** Types et constantes compiles sans erreur TypeScript.

---

## Etape 3 : Client API & Authentification

### 3.1 Client API pour l'extension

```typescript
// src/shared/api-client.ts

import { API_BASE_URL, STORAGE_KEYS } from './constants'
import type { AuthResponse, LoginRequest } from './types'

class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = API_BASE_URL
  }

  /**
   * Recupere le JWT depuis chrome.storage.session
   */
  private async getToken(): Promise<string | null> {
    const result = await chrome.storage.session.get(STORAGE_KEYS.TOKEN)
    return result[STORAGE_KEYS.TOKEN] || null
  }

  /**
   * Requete HTTP generique avec gestion JWT
   */
  async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options: { skipAuth?: boolean } = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (!options.skipAuth) {
      const token = await this.getToken()
      if (!token) {
        throw new ApiError('Non authentifie', 401)
      }
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.detail || `Erreur ${response.status}`,
        response.status
      )
    }

    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  // Raccourcis
  get<T>(path: string) { return this.request<T>('GET', path) }
  post<T>(path: string, body?: unknown) { return this.request<T>('POST', path, body) }
  put<T>(path: string, body?: unknown) { return this.request<T>('PUT', path, body) }
  del<T>(path: string) { return this.request<T>('DELETE', path) }

  // Auth (pas besoin de token)
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>('POST', '/api/auth/login', credentials, { skipAuth: true })
  }
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

export const apiClient = new ApiClient()
```

### 3.2 Gestionnaire d'authentification

```typescript
// src/shared/auth.ts

import { apiClient, ApiError } from './api-client'
import { STORAGE_KEYS } from './constants'
import type { User, LoginRequest, AuthResponse, SyncedData } from './types'

class AuthManager {

  /**
   * Connexion avec email/password
   * Stocke le token dans chrome.storage.session (plus securise)
   * Stocke l'utilisateur dans chrome.storage.local (persistant)
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.login(credentials)

    // Token en session (efface a la fermeture du navigateur)
    await chrome.storage.session.set({
      [STORAGE_KEYS.TOKEN]: response.access_token,
    })

    // User en local (persistant entre les sessions)
    await chrome.storage.local.set({
      [STORAGE_KEYS.USER]: response.user,
    })

    return response
  }

  /**
   * Deconnexion
   */
  async logout(): Promise<void> {
    await chrome.storage.session.remove(STORAGE_KEYS.TOKEN)
    await chrome.storage.local.remove([
      STORAGE_KEYS.USER,
      STORAGE_KEYS.SYNCED_DATA,
      STORAGE_KEYS.ACTIVE_APPLICATION,
    ])
  }

  /**
   * Verifie si l'utilisateur est connecte et le token valide
   */
  async checkAuth(): Promise<User | null> {
    try {
      const tokenResult = await chrome.storage.session.get(STORAGE_KEYS.TOKEN)
      if (!tokenResult[STORAGE_KEYS.TOKEN]) {
        return null
      }

      // Verifier le token aupres du backend
      const user = await apiClient.get<User>('/api/auth/me')
      await chrome.storage.local.set({ [STORAGE_KEYS.USER]: user })
      return user
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        await this.logout()
      }
      return null
    }
  }

  /**
   * Recupere l'utilisateur depuis le cache local
   */
  async getCachedUser(): Promise<User | null> {
    const result = await chrome.storage.local.get(STORAGE_KEYS.USER)
    return result[STORAGE_KEYS.USER] || null
  }

  /**
   * Verifie si un token existe (sans verifier sa validite)
   */
  async hasToken(): Promise<boolean> {
    const result = await chrome.storage.session.get(STORAGE_KEYS.TOKEN)
    return !!result[STORAGE_KEYS.TOKEN]
  }
}

export const authManager = new AuthManager()
```

### 3.3 Gestionnaire de stockage

```typescript
// src/shared/storage.ts

import { STORAGE_KEYS, CACHE_TTL } from './constants'
import type { SyncedData, FundSiteConfig } from './types'

class StorageManager {
  /**
   * Sauvegarde les donnees synchronisees avec timestamp
   */
  async saveSyncedData(data: Omit<SyncedData, 'last_synced'>): Promise<void> {
    const syncedData: SyncedData = {
      ...data,
      last_synced: new Date().toISOString(),
    }
    await chrome.storage.local.set({
      [STORAGE_KEYS.SYNCED_DATA]: syncedData,
    })
  }

  /**
   * Recupere les donnees synchronisees si encore valides
   */
  async getSyncedData(): Promise<SyncedData | null> {
    const result = await chrome.storage.local.get(STORAGE_KEYS.SYNCED_DATA)
    const data = result[STORAGE_KEYS.SYNCED_DATA] as SyncedData | undefined

    if (!data) return null

    // Verifier la fraicheur du cache
    const age = Date.now() - new Date(data.last_synced).getTime()
    if (age > CACHE_TTL.SYNCED_DATA) {
      return null // Cache expire
    }

    return data
  }

  /**
   * Force le rafraichissement au prochain acces
   */
  async invalidateCache(): Promise<void> {
    await chrome.storage.local.remove(STORAGE_KEYS.SYNCED_DATA)
  }

  /**
   * Sauvegarde les configs de sites de fonds
   */
  async saveFundConfigs(configs: FundSiteConfig[]): Promise<void> {
    await chrome.storage.local.set({
      [STORAGE_KEYS.FUND_CONFIGS]: {
        configs,
        cached_at: new Date().toISOString(),
      },
    })
  }

  /**
   * Recupere les configs de sites de fonds
   */
  async getFundConfigs(): Promise<FundSiteConfig[] | null> {
    const result = await chrome.storage.local.get(STORAGE_KEYS.FUND_CONFIGS)
    const data = result[STORAGE_KEYS.FUND_CONFIGS]

    if (!data) return null

    const age = Date.now() - new Date(data.cached_at).getTime()
    if (age > CACHE_TTL.FUND_CONFIGS) {
      return null
    }

    return data.configs
  }
}

export const storageManager = new StorageManager()
```

**Critere de validation :** Login depuis le popup → token stocke dans `chrome.storage.session` → `checkAuth()` retourne l'utilisateur.

---

## Etape 4 : Service Worker (Background)

### 4.1 Service Worker principal

```typescript
// src/background/service-worker.ts

import { authManager } from '@shared/auth'
import { apiClient } from '@shared/api-client'
import { storageManager } from '@shared/storage'
import { CACHE_TTL } from '@shared/constants'
import type {
  ExtensionMessage,
  SyncedData,
  Entreprise,
  FundSiteConfig,
  FundApplication,
} from '@shared/types'

// ========================================
// Initialisation
// ========================================

chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === 'install') {
    console.log('[ESG Advisor] Extension installee')
    // Ouvrir le popup pour la premiere connexion
  }
})

// ========================================
// Gestion des messages
// ========================================

chrome.runtime.onMessage.addListener((message: ExtensionMessage, sender, sendResponse) => {
  handleMessage(message, sender).then(sendResponse)
  return true // Indique une reponse asynchrone
})

async function handleMessage(
  message: ExtensionMessage,
  sender: chrome.runtime.MessageSender
): Promise<unknown> {
  switch (message.type) {
    case 'AUTH_STATUS':
      return handleAuthStatus()

    case 'SYNC_DATA':
      return handleSyncData()

    case 'FUND_DETECTED':
      return handleFundDetected(message.payload as { url: string, tabId: number })

    case 'GET_COMPANY_DATA':
      return handleGetCompanyData()

    case 'FIELD_SUGGESTION':
      return handleFieldSuggestion(message.payload as {
        fonds_id: string
        field_name: string
        field_label: string
        context: string
      })

    case 'SAVE_PROGRESS':
      return handleSaveProgress(message.payload as {
        application_id: string
        form_data: Record<string, unknown>
        current_step: number
      })

    default:
      console.warn('[ESG Advisor] Message inconnu:', message.type)
      return null
  }
}

// ========================================
// Handlers
// ========================================

async function handleAuthStatus() {
  const user = await authManager.checkAuth()
  return { authenticated: !!user, user }
}

async function handleSyncData(): Promise<SyncedData | null> {
  // Verifier le cache d'abord
  const cached = await storageManager.getSyncedData()
  if (cached) return cached

  // Sinon, synchroniser depuis le backend
  try {
    const user = await authManager.checkAuth()
    if (!user) return null

    const [entreprises, applications] = await Promise.all([
      apiClient.get<Entreprise[]>('/api/entreprises/'),
      apiClient.get<FundApplication[]>('/api/extension/applications').catch(() => []),
    ])

    const entreprise = entreprises[0] || null

    let scores = []
    let documents = []
    let fonds = []

    if (entreprise) {
      ;[scores, documents, fonds] = await Promise.all([
        apiClient.get(`/api/entreprises/${entreprise.id}/scores`).catch(() => []),
        apiClient.get(`/api/documents/entreprise/${entreprise.id}`).catch(() => []),
        apiClient.get('/api/extension/fund-recommendations').catch(() => []),
      ])
    }

    const syncedData = {
      user,
      entreprise,
      scores,
      documents,
      fonds_recommandes: fonds,
      applications,
    }

    await storageManager.saveSyncedData(syncedData)
    return { ...syncedData, last_synced: new Date().toISOString() }
  } catch (error) {
    console.error('[ESG Advisor] Erreur de synchronisation:', error)
    return null
  }
}

async function handleFundDetected(payload: { url: string, tabId: number }) {
  const configs = await getFundConfigs()
  const matchedConfig = configs.find(config =>
    config.url_patterns.some(pattern => matchUrl(payload.url, pattern))
  )

  if (matchedConfig) {
    // Afficher le badge sur l'icone
    chrome.action.setBadgeText({ text: '!', tabId: payload.tabId })
    chrome.action.setBadgeBackgroundColor({ color: '#059669', tabId: payload.tabId })

    // Envoyer une notification si premiere detection
    chrome.notifications.create(`fund-${matchedConfig.fonds_id}`, {
      type: 'basic',
      iconUrl: 'assets/icons/icon-128.png',
      title: 'Fonds vert detecte !',
      message: `${matchedConfig.fonds_nom} - Cliquez pour etre guide dans votre candidature`,
    })

    return { detected: true, config: matchedConfig }
  }

  return { detected: false }
}

async function handleGetCompanyData() {
  const data = await storageManager.getSyncedData()
  if (!data) {
    return handleSyncData()
  }
  return data
}

async function handleFieldSuggestion(payload: {
  fonds_id: string
  field_name: string
  field_label: string
  context: string
}) {
  try {
    const response = await apiClient.post<{ suggestion: string }>(
      '/api/extension/field-suggest',
      payload
    )
    return response
  } catch (error) {
    console.error('[ESG Advisor] Erreur suggestion:', error)
    return { suggestion: null, error: 'Impossible de generer une suggestion' }
  }
}

async function handleSaveProgress(payload: {
  application_id: string
  form_data: Record<string, unknown>
  current_step: number
}) {
  try {
    return await apiClient.post('/api/extension/progress', payload)
  } catch (error) {
    console.error('[ESG Advisor] Erreur sauvegarde:', error)
    return { error: 'Impossible de sauvegarder' }
  }
}

// ========================================
// Utilitaires
// ========================================

async function getFundConfigs(): Promise<FundSiteConfig[]> {
  const cached = await storageManager.getFundConfigs()
  if (cached) return cached

  try {
    const configs = await apiClient.get<FundSiteConfig[]>('/api/extension/fund-configs')
    await storageManager.saveFundConfigs(configs)
    return configs
  } catch {
    return []
  }
}

function matchUrl(url: string, pattern: string): boolean {
  // Convertir le pattern glob en regex
  const regex = new RegExp(
    '^' + pattern
      .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
      .replace(/\*/g, '.*')
    + '$'
  )
  return regex.test(url)
}

// ========================================
// Alarmes periodiques
// ========================================

// Verification du token toutes les 30 minutes
chrome.alarms.create('check-auth', { periodInMinutes: 30 })

// Synchronisation des donnees toutes les 5 minutes
chrome.alarms.create('sync-data', { periodInMinutes: 5 })

chrome.alarms.onAlarm.addListener(async (alarm) => {
  switch (alarm.name) {
    case 'check-auth':
      await authManager.checkAuth()
      break
    case 'sync-data':
      await handleSyncData()
      break
  }
})

// Ecouter les clics sur les notifications
chrome.notifications.onClicked.addListener(async (notificationId) => {
  if (notificationId.startsWith('fund-')) {
    // Ouvrir le side panel
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (tab?.id) {
      chrome.sidePanel.open({ tabId: tab.id })
    }
  }
})
```

**Critere de validation :** Le service worker demarre, gere les messages, et synchronise les donnees avec le backend.

---

## Etape 5 : Popup (Interface Principale)

### 5.1 Point d'entree Popup

```html
<!-- src/popup/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESG Advisor Guide</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="./main.ts"></script>
</body>
</html>
```

```typescript
// src/popup/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import '../../assets/styles/main.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
```

### 5.2 Composant Principal Popup

Le popup fait 400px x 500px et affiche soit :
- **LoginPanel** si non connecte
- **DashboardPanel** si connecte (avec liste des candidatures, fonds recommandes, raccourcis)

```vue
<!-- src/popup/App.vue -->
<template>
  <div class="w-[400px] min-h-[500px] bg-gray-50 flex flex-col">
    <!-- Header -->
    <header class="bg-emerald-600 text-white px-4 py-3 flex items-center gap-3">
      <img src="../assets/icons/icon-32.png" alt="ESG" class="w-8 h-8">
      <div>
        <h1 class="text-lg font-bold leading-tight">ESG Advisor</h1>
        <p class="text-emerald-100 text-xs">Guide Fonds Verts</p>
      </div>
      <button
        v-if="isAuthenticated"
        @click="handleLogout"
        class="ml-auto text-emerald-200 hover:text-white text-sm"
      >
        Deconnexion
      </button>
    </header>

    <!-- Contenu -->
    <main class="flex-1 overflow-y-auto">
      <LoginPanel v-if="!isAuthenticated" @login-success="onLoginSuccess" />
      <DashboardPanel v-else :data="syncedData" :loading="syncing" @refresh="syncData" />
    </main>

    <!-- Footer -->
    <footer class="border-t border-gray-200 px-4 py-2 bg-white">
      <a
        href="http://localhost:5173"
        target="_blank"
        class="text-xs text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
      >
        Ouvrir la plateforme ESG Advisor
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>
    </footer>
  </div>
</template>
```

### 5.3 LoginPanel

```vue
<!-- src/popup/components/LoginPanel.vue -->
<template>
  <div class="p-6 flex flex-col items-center">
    <!-- Logo / Illustration -->
    <div class="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
      <svg class="w-10 h-10 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955
              11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29
              9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    </div>

    <h2 class="text-lg font-semibold text-gray-800 mb-1">Connectez-vous</h2>
    <p class="text-sm text-gray-500 mb-6 text-center">
      Utilisez vos identifiants ESG Advisor
    </p>

    <form @submit.prevent="handleLogin" class="w-full space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          v-model="email"
          type="email"
          required
          placeholder="votre@email.com"
          class="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm
                 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
        >
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
        <input
          v-model="password"
          type="password"
          required
          placeholder="Votre mot de passe"
          class="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm
                 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
        >
      </div>

      <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-emerald-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium
               hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
               flex items-center justify-center gap-2"
      >
        <span v-if="loading" class="w-4 h-4 border-2 border-white border-t-transparent
                                     rounded-full animate-spin"></span>
        {{ loading ? 'Connexion...' : 'Se connecter' }}
      </button>
    </form>

    <p class="mt-4 text-xs text-gray-400 text-center">
      Pas encore de compte ?
      <a href="http://localhost:5173/register" target="_blank"
         class="text-emerald-600 hover:underline">
        Inscrivez-vous sur la plateforme
      </a>
    </p>
  </div>
</template>
```

### 5.4 DashboardPanel

```vue
<!-- src/popup/components/DashboardPanel.vue -->
<!-- Affiche :
  - Carte entreprise avec score ESG global
  - Liste des candidatures en cours (ApplicationCard)
  - Fonds recommandes (FundRecommendation)
  - Bouton "Synchroniser"
-->
<template>
  <div class="p-4 space-y-4">
    <!-- Carte Entreprise -->
    <div v-if="data?.entreprise" class="bg-white rounded-xl border border-gray-200 p-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
          <span class="text-emerald-700 font-bold text-sm">
            {{ data.entreprise.nom.substring(0, 2).toUpperCase() }}
          </span>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-gray-800 text-sm truncate">
            {{ data.entreprise.nom }}
          </h3>
          <p class="text-xs text-gray-500">
            {{ data.entreprise.secteur || 'Secteur non defini' }} · {{ data.entreprise.pays }}
          </p>
        </div>
        <div v-if="latestScore" class="text-right">
          <div class="text-lg font-bold" :class="scoreColor">
            {{ latestScore.score_global }}/100
          </div>
          <div class="text-xs text-gray-500">Score ESG</div>
        </div>
      </div>
    </div>

    <!-- Candidatures en cours -->
    <section>
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-800 text-sm">Candidatures en cours</h3>
        <span class="text-xs text-gray-400">{{ activeApplications.length }}</span>
      </div>

      <div v-if="activeApplications.length === 0"
           class="bg-white rounded-xl border border-dashed border-gray-300 p-4 text-center">
        <p class="text-sm text-gray-500">Aucune candidature en cours</p>
        <p class="text-xs text-gray-400 mt-1">
          Naviguez vers un site de fonds vert pour commencer
        </p>
      </div>

      <div v-else class="space-y-2">
        <ApplicationCard
          v-for="app in activeApplications"
          :key="app.id"
          :application="app"
        />
      </div>
    </section>

    <!-- Fonds recommandes -->
    <section v-if="data?.fonds_recommandes?.length">
      <h3 class="font-semibold text-gray-800 text-sm mb-2">Fonds recommandes</h3>
      <div class="space-y-2">
        <FundRecommendation
          v-for="fonds in data.fonds_recommandes.slice(0, 3)"
          :key="fonds.id"
          :fonds="fonds"
        />
      </div>
    </section>

    <!-- Derniere synchro -->
    <div class="flex items-center justify-between text-xs text-gray-400 pt-2">
      <span v-if="data?.last_synced">
        Maj : {{ formatRelativeTime(data.last_synced) }}
      </span>
      <button
        @click="$emit('refresh')"
        :disabled="loading"
        class="text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
      >
        <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }"
             fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11
                11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Actualiser
      </button>
    </div>
  </div>
</template>
```

### 5.5 ApplicationCard & FundRecommendation

Composants compacts pour le popup :

```vue
<!-- src/popup/components/ApplicationCard.vue -->
<!-- Affiche : nom du fonds, institution, barre de progression, statut -->
<template>
  <div class="bg-white rounded-lg border border-gray-200 p-3 hover:border-emerald-300
              transition-colors cursor-pointer" @click="openApplication">
    <div class="flex items-start gap-2">
      <div class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold"
           :class="statusClasses">
        {{ application.progress_pct }}%
      </div>
      <div class="flex-1 min-w-0">
        <h4 class="text-sm font-medium text-gray-800 truncate">
          {{ application.fonds_nom }}
        </h4>
        <p class="text-xs text-gray-500 truncate">{{ application.fonds_institution }}</p>
        <!-- Barre de progression -->
        <div class="mt-1.5 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
               :class="progressBarColor"
               :style="{ width: application.progress_pct + '%' }">
          </div>
        </div>
      </div>
      <span class="text-xs px-2 py-0.5 rounded-full" :class="statusBadgeClasses">
        {{ statusLabel }}
      </span>
    </div>
  </div>
</template>
```

```vue
<!-- src/popup/components/FundRecommendation.vue -->
<!-- Affiche : nom du fonds, montant, compatibilite, bouton "Postuler" -->
<template>
  <div class="bg-white rounded-lg border border-gray-200 p-3">
    <div class="flex items-center gap-2">
      <div class="flex-1 min-w-0">
        <h4 class="text-sm font-medium text-gray-800 truncate">{{ fonds.nom }}</h4>
        <p class="text-xs text-gray-500">
          {{ fonds.institution }} · {{ formatMontant(fonds.montant_min, fonds.montant_max, fonds.devise) }}
        </p>
      </div>
      <a v-if="fonds.url_source"
         :href="fonds.url_source"
         target="_blank"
         class="text-xs bg-emerald-50 text-emerald-700 px-3 py-1 rounded-lg
                hover:bg-emerald-100 transition-colors whitespace-nowrap">
        Postuler
      </a>
    </div>
  </div>
</template>
```

**Critere de validation :** Le popup s'ouvre, permet de se connecter, affiche le dashboard avec les donnees de la plateforme.

---

## Etape 6 : Nouveaux Endpoints Backend

### 6.1 Modeles de donnees

Creer les modeles `FundApplication` et `FundSiteConfig` dans le backend.

```bash
# Fichier : backend/app/models/fund_application.py
# Migration : alembic revision --autogenerate -m "add fund_applications and fund_site_configs"
# Appliquer : alembic upgrade head
```

### 6.2 API Extension

```python
# backend/app/api/extension.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.entreprise import Entreprise
from app.models.fonds_vert import FondsVert
from app.models.fund_application import FundApplication, FundSiteConfig

router = APIRouter(prefix="/api/extension", tags=["extension"])

# GET /fund-configs - Configs des sites de fonds
@router.get("/fund-configs")
async def get_fund_configs(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Retourne les configurations de sites de fonds actives"""
    query = (
        select(FundSiteConfig, FondsVert.nom)
        .join(FondsVert, FundSiteConfig.fonds_id == FondsVert.id)
        .where(FundSiteConfig.is_active == True)
    )
    result = await session.execute(query)
    configs = []
    for config, fonds_nom in result.all():
        configs.append({
            **config.to_dict(),
            "fonds_nom": fonds_nom,
        })
    return configs

# GET /applications - Liste des candidatures
@router.get("/applications")
async def list_applications(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Liste les candidatures de l'utilisateur"""
    # Trouver les entreprises de l'utilisateur
    entreprises = await session.execute(
        select(Entreprise.id).where(Entreprise.user_id == user.id)
    )
    entreprise_ids = [e.id for e in entreprises.scalars().all()]

    if not entreprise_ids:
        return []

    query = (
        select(FundApplication, FondsVert.nom, FondsVert.institution)
        .outerjoin(FondsVert, FundApplication.fonds_id == FondsVert.id)
        .where(FundApplication.entreprise_id.in_(entreprise_ids))
        .order_by(FundApplication.updated_at.desc())
    )
    result = await session.execute(query)
    return [
        {
            **app.to_dict(),
            "fonds_nom": nom or "Fonds inconnu",
            "fonds_institution": institution or "",
        }
        for app, nom, institution in result.all()
    ]

# POST /applications - Creer/mettre a jour une candidature
@router.post("/applications", status_code=201)
async def create_application(
    data: dict,  # Schema a definir
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Cree une nouvelle candidature"""
    application = FundApplication(**data)
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application

# POST /field-suggest - Suggestion IA pour un champ
@router.post("/field-suggest")
async def suggest_field(
    data: dict,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Utilise le LLM pour suggerer le contenu d'un champ de formulaire"""
    # Recuperer le contexte entreprise
    entreprise = await session.execute(
        select(Entreprise).where(Entreprise.user_id == user.id)
    )
    entreprise = entreprise.scalar_one_or_none()

    if not entreprise:
        raise HTTPException(404, "Aucune entreprise trouvee")

    # Appeler le LLM via OpenRouter
    from app.agent.engine import get_llm_client

    client = get_llm_client()
    prompt = f"""Tu es un assistant specialise dans les candidatures aux fonds verts africains.

Contexte de l'entreprise :
- Nom : {entreprise.nom}
- Secteur : {entreprise.secteur}
- Pays : {entreprise.pays}
- Description : {entreprise.description or 'Non disponible'}

Le champ a remplir est : "{data.get('field_label', '')}"
Contexte supplementaire : {data.get('context', '')}

Genere une reponse appropriee pour ce champ de formulaire.
La reponse doit etre professionnelle, concise et adaptee au contexte ESG/fonds vert.
Reponds uniquement avec le texte a inserer dans le champ, sans explication."""

    response = await client.chat.completions.create(
        model="anthropic/claude-sonnet-4-5-20250514",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )

    return {"suggestion": response.choices[0].message.content}

# POST /progress - Sauvegarder la progression
@router.post("/progress")
async def save_progress(
    data: dict,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Sauvegarde l'etat du formulaire"""
    application = await session.get(FundApplication, data["application_id"])
    if not application:
        raise HTTPException(404, "Candidature non trouvee")

    application.form_data = data.get("form_data", {})
    application.current_step = data.get("current_step", 0)
    application.progress_pct = data.get("progress_pct", application.progress_pct)

    await session.commit()
    return {"status": "ok"}
```

### 6.3 Enregistrer le routeur

```python
# Dans backend/app/main.py, ajouter :
from app.api.extension import router as extension_router
app.include_router(extension_router)
```

**Critere de validation :** Les endpoints `/api/extension/*` repondent correctement. Tests avec `curl` ou depuis le popup.

---

## Etape 7 : Seed des Configurations de Sites

### 7.1 Donnees initiales

```json
// data/fund_site_configs.json
[
  {
    "fonds_code": "boad_facilite_verte",
    "url_patterns": [
      "https://www.boad.org/*appel*",
      "https://www.boad.org/*projet*",
      "https://apply.boad.org/*"
    ],
    "steps": [
      {
        "order": 1,
        "title": "Informations sur l'entreprise",
        "description": "Renseignez les informations de base de votre PME",
        "url_pattern": null,
        "fields": [
          {
            "selector": "[name='company_name'], #company-name, [data-field='nom']",
            "label": "Nom de l'entreprise",
            "source": "entreprise.nom",
            "help_text": "Le nom legal tel qu'il figure sur votre registre de commerce",
            "type": "text",
            "required": true,
            "ai_suggest": false
          },
          {
            "selector": "[name='sector'], #sector, [data-field='secteur']",
            "label": "Secteur d'activite",
            "source": "entreprise.secteur",
            "help_text": "Votre secteur principal. Les fonds privilegient: agriculture, energie renouvelable, recyclage",
            "type": "select",
            "required": true,
            "ai_suggest": false
          },
          {
            "selector": "[name='country'], #country",
            "label": "Pays",
            "source": "entreprise.pays",
            "help_text": "Le pays d'immatriculation de votre entreprise",
            "type": "select",
            "required": true,
            "ai_suggest": false
          },
          {
            "selector": "[name='description'], #project-description, textarea[name='project']",
            "label": "Description du projet",
            "source": null,
            "help_text": "Decrivez votre projet vert en mettant en avant l'impact environnemental et social",
            "type": "textarea",
            "required": true,
            "ai_suggest": true
          }
        ]
      },
      {
        "order": 2,
        "title": "Informations financieres",
        "description": "Presentez la situation financiere de votre entreprise",
        "url_pattern": null,
        "fields": [
          {
            "selector": "[name='revenue'], #chiffre-affaires",
            "label": "Chiffre d'affaires annuel",
            "source": "entreprise.chiffre_affaires",
            "help_text": "Votre CA du dernier exercice cloture, en devise locale",
            "type": "number",
            "required": true,
            "ai_suggest": false
          },
          {
            "selector": "[name='employees'], #effectifs",
            "label": "Nombre d'employes",
            "source": "entreprise.effectifs",
            "help_text": "Le nombre total de salaries (CDI + CDD)",
            "type": "number",
            "required": true,
            "ai_suggest": false
          },
          {
            "selector": "[name='montant_demande'], #amount-requested",
            "label": "Montant demande",
            "source": null,
            "help_text": "Le montant doit etre entre 50M et 2Mds XOF pour ce fonds",
            "type": "number",
            "required": true,
            "ai_suggest": false
          }
        ]
      },
      {
        "order": 3,
        "title": "Impact ESG",
        "description": "Detaillez l'impact environnemental et social de votre projet",
        "url_pattern": null,
        "fields": [
          {
            "selector": "[name='environmental_impact'], #impact-env",
            "label": "Impact environnemental",
            "source": null,
            "help_text": "Decrivez les benefices environnementaux : reduction CO2, gestion dechets, eau...",
            "type": "textarea",
            "required": true,
            "ai_suggest": true
          },
          {
            "selector": "[name='social_impact'], #impact-social",
            "label": "Impact social",
            "source": null,
            "help_text": "Emplois crees, formation, inclusion des femmes/jeunes, benefice communautaire",
            "type": "textarea",
            "required": true,
            "ai_suggest": true
          },
          {
            "selector": "[name='governance'], #gouvernance",
            "label": "Pratiques de gouvernance",
            "source": null,
            "help_text": "Transparence, conformite, politique anti-corruption, reporting ESG",
            "type": "textarea",
            "required": true,
            "ai_suggest": true
          }
        ]
      },
      {
        "order": 4,
        "title": "Documents justificatifs",
        "description": "Telechargez les documents requis pour votre candidature",
        "url_pattern": null,
        "fields": [
          {
            "selector": "[name='doc_rccm'], #upload-rccm",
            "label": "Registre de commerce (RCCM)",
            "source": null,
            "help_text": "Copie certifiee de votre RCCM datant de moins de 3 mois",
            "type": "file",
            "required": true,
            "ai_suggest": false
          },
          {
            "selector": "[name='doc_bilan'], #upload-bilan",
            "label": "Bilan comptable",
            "source": null,
            "help_text": "Les 2 derniers bilans certifies par un expert-comptable agree",
            "type": "file",
            "required": true,
            "ai_suggest": false
          },
          {
            "selector": "[name='doc_esg'], #upload-esg-report",
            "label": "Rapport ESG",
            "source": null,
            "help_text": "Vous pouvez generer ce rapport depuis la plateforme ESG Advisor",
            "type": "file",
            "required": false,
            "ai_suggest": false
          }
        ]
      },
      {
        "order": 5,
        "title": "Validation et soumission",
        "description": "Verifiez vos informations et soumettez votre candidature",
        "url_pattern": null,
        "fields": []
      }
    ],
    "required_docs": [
      {
        "name": "Registre de commerce (RCCM)",
        "type": "legal",
        "format": "PDF",
        "description": "Copie certifiee datant de moins de 3 mois"
      },
      {
        "name": "Bilans comptables (2 derniers exercices)",
        "type": "financial",
        "format": "PDF",
        "description": "Certifies par un expert-comptable agree"
      },
      {
        "name": "Rapport ESG / Bilan carbone",
        "type": "esg",
        "format": "PDF",
        "description": "Generable depuis la plateforme ESG Advisor"
      },
      {
        "name": "Business plan du projet vert",
        "type": "technical",
        "format": "PDF/DOCX",
        "description": "Description detaillee du projet, objectifs, budget, calendrier"
      },
      {
        "name": "Attestation de regularite fiscale",
        "type": "legal",
        "format": "PDF",
        "description": "Delivree par l'administration fiscale du pays"
      }
    ],
    "tips": {
      "general": "La BOAD privilegie les projets avec un fort impact environnemental dans la zone UEMOA",
      "description": "Mettez en avant les Objectifs de Developpement Durable (ODD) concernes",
      "financial": "Montrez la viabilite financiere du projet meme sans le financement vert"
    }
  }
]
```

**Critere de validation :** Le seed cree les configs en DB, le endpoint `/api/extension/fund-configs` les retourne.

---

## Resume Semaine 1

| Jour | Taches | Livrable |
|------|--------|----------|
| J1 | Init projet, Manifest V3, config Vite | Build fonctionnel |
| J2 | Types, constantes, client API | Couche communication |
| J3 | Auth manager, storage manager | Login fonctionnel |
| J4 | Service worker, gestion messages | Background operationnel |
| J5 | Popup (Login + Dashboard), endpoints backend | Extension installable |

### Checklist de fin de semaine

- [ ] `npm run build` produit un dossier `dist/` valide
- [ ] L'extension s'installe dans Chrome (`chrome://extensions` mode developpeur)
- [ ] Le popup s'ouvre et permet de se connecter
- [ ] Apres connexion, le dashboard affiche les donnees de la plateforme
- [ ] Le service worker tourne et synchronise les donnees
- [ ] Les endpoints `/api/extension/*` repondent correctement
- [ ] Les modeles `FundApplication` et `FundSiteConfig` sont migres
- [ ] Le seed des configs de fonds fonctionne
