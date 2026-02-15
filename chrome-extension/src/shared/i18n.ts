/**
 * Wrapper pour chrome.i18n.getMessage
 * Usage dans les templates : {{ t('login_title') }}
 */
export function t(key: string, ...substitutions: string[]): string {
  return chrome.i18n.getMessage(key, substitutions) || key
}

/**
 * Composable Vue pour l'i18n
 */
export function useI18n() {
  return { t }
}
