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
