import { storageManager } from '@shared/storage'

/**
 * Verifie les deadlines des fonds et les rappels de candidatures
 * Execute toutes les 6 heures
 */
export async function checkDeadlinesAndReminders() {
  const data = await storageManager.getSyncedData()
  if (!data) return

  const now = new Date()

  // 1. Verifier les deadlines des fonds recommandes
  for (const fonds of data.fonds_recommandes || []) {
    if (!fonds.date_limite) continue

    const deadline = new Date(fonds.date_limite)
    const daysUntil = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

    if ([30, 7, 1].includes(daysUntil)) {
      const notifId = `deadline-${fonds.id}-${daysUntil}`
      const existing = await getShownNotification(notifId)
      if (existing) continue

      chrome.notifications.create(notifId, {
        type: 'basic',
        iconUrl: 'assets/icons/icon-128.png',
        title: daysUntil === 1
          ? 'Dernier jour pour postuler !'
          : `Date limite dans ${daysUntil} jours`,
        message: `${fonds.nom} (${fonds.institution}) — Date limite : ${deadline.toLocaleDateString('fr-FR')}`,
        priority: daysUntil <= 7 ? 2 : 1,
      })

      await markNotificationShown(notifId)
    }
  }

  // 2. Rappels pour les candidatures inactives
  for (const app of data.applications || []) {
    if (!['brouillon', 'en_cours'].includes(app.status)) continue

    const lastUpdate = new Date(app.updated_at || app.started_at)
    const daysSinceUpdate = Math.ceil(
      (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60 * 24)
    )

    if (daysSinceUpdate >= 3) {
      const notifId = `reminder-${app.id}-${Math.floor(daysSinceUpdate / 3)}`
      const existing = await getShownNotification(notifId)
      if (existing) continue

      chrome.notifications.create(notifId, {
        type: 'basic',
        iconUrl: 'assets/icons/icon-128.png',
        title: 'Candidature en attente',
        message: `Votre candidature "${app.fonds_nom}" est a ${app.progress_pct}%. Reprenez ou vous en etes !`,
        priority: 1,
      })

      await markNotificationShown(notifId)
    }
  }
}

async function getShownNotification(id: string): Promise<boolean> {
  const result = await chrome.storage.local.get('shown_notifications')
  const shown = result.shown_notifications || {}
  return !!shown[id]
}

async function markNotificationShown(id: string): Promise<void> {
  const result = await chrome.storage.local.get('shown_notifications')
  const shown = result.shown_notifications || {}
  shown[id] = Date.now()

  // Nettoyer les vieilles notifications (> 30 jours)
  const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000
  for (const [key, timestamp] of Object.entries(shown)) {
    if ((timestamp as number) < thirtyDaysAgo) {
      delete shown[key]
    }
  }

  await chrome.storage.local.set({ shown_notifications: shown })
}
