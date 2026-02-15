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
  mode_acces: string | null
  is_active: boolean
  compatibility_score?: number
}

// === Candidature ===
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

// === Config Site Fonds ===
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
  source: string | null
  help_text: string
  type: 'text' | 'number' | 'select' | 'textarea' | 'file' | 'date'
  required: boolean
  ai_suggest: boolean
}

export interface RequiredDoc {
  name: string
  type: string
  format: string
  description: string
  available_on_platform: boolean
  document_id: string | null
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
  | 'GET_FUND_CONFIGS'
  | 'AUTOFILL_FIELD'
  | 'HIGHLIGHT_FIELDS'
  | 'BATCH_AUTOFILL'

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
