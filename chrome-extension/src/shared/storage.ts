import { STORAGE_KEYS, CACHE_TTL } from './constants'
import type { SyncedData, FundSiteConfig } from './types'

class StorageManager {
  async saveSyncedData(data: Omit<SyncedData, 'last_synced'>): Promise<void> {
    const syncedData: SyncedData = {
      ...data,
      last_synced: new Date().toISOString(),
    }
    await chrome.storage.local.set({
      [STORAGE_KEYS.SYNCED_DATA]: syncedData,
    })
  }

  async getSyncedData(): Promise<SyncedData | null> {
    const result = await chrome.storage.local.get(STORAGE_KEYS.SYNCED_DATA)
    const data = result[STORAGE_KEYS.SYNCED_DATA] as SyncedData | undefined

    if (!data) return null

    const age = Date.now() - new Date(data.last_synced).getTime()
    if (age > CACHE_TTL.SYNCED_DATA) {
      return null
    }

    return data
  }

  async invalidateCache(): Promise<void> {
    await chrome.storage.local.remove(STORAGE_KEYS.SYNCED_DATA)
  }

  async saveFundConfigs(configs: FundSiteConfig[]): Promise<void> {
    await chrome.storage.local.set({
      [STORAGE_KEYS.FUND_CONFIGS]: {
        configs,
        cached_at: new Date().toISOString(),
      },
    })
  }

  async getFundConfigs(): Promise<FundSiteConfig[] | null> {
    const result = await chrome.storage.local.get(STORAGE_KEYS.FUND_CONFIGS)
    const data = result[STORAGE_KEYS.FUND_CONFIGS] as { configs: FundSiteConfig[], cached_at: string } | undefined

    if (!data) return null

    const age = Date.now() - new Date(data.cached_at).getTime()
    if (age > CACHE_TTL.FUND_CONFIGS) {
      return null
    }

    return data.configs
  }
}

export const storageManager = new StorageManager()
