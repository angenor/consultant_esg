/**
 * Ecoute les messages du Side Panel pour remplir les champs
 */
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'AUTOFILL_FIELD') {
    const { selector, value } = message.payload

    // Trouver l'element
    const selectors = selector.split(',').map((s: string) => s.trim())
    let element: HTMLElement | null = null

    for (const sel of selectors) {
      try {
        element = document.querySelector<HTMLElement>(sel)
        if (element) break
      } catch {
        /* selecteur invalide, continuer */
      }
    }

    if (!element) {
      sendResponse({ success: false, error: 'Element non trouve' })
      return
    }

    // Remplir selon le type d'element
    if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
      // Simuler une saisie naturelle
      element.focus()
      element.value = value

      // Declencher les evenements pour que les frameworks JS detectent le changement
      element.dispatchEvent(new Event('input', { bubbles: true }))
      element.dispatchEvent(new Event('change', { bubbles: true }))
      element.dispatchEvent(new Event('blur', { bubbles: true }))

      // Animation de confirmation
      element.style.transition = 'background-color 0.3s'
      element.style.backgroundColor = '#f0fdf4'
      setTimeout(() => {
        element!.style.backgroundColor = ''
      }, 1000)

      sendResponse({ success: true })
    } else if (element instanceof HTMLSelectElement) {
      // Pour les selects, chercher l'option correspondante
      const option = Array.from(element.options).find(
        opt => opt.value === value || opt.text.toLowerCase().includes(value.toLowerCase())
      )
      if (option) {
        element.value = option.value
        element.dispatchEvent(new Event('change', { bubbles: true }))
        sendResponse({ success: true })
      } else {
        sendResponse({ success: false, error: 'Option non trouvee' })
      }
    }
  }

  if (message.type === 'HIGHLIGHT_FIELDS') {
    const { step, companyData } = message.payload
    // Importer dynamiquement le highlighter pour eviter le chargement initial
    import('./highlighter').then(({ fieldHighlighter }) => {
      fieldHighlighter.highlightStep(step, companyData)
    })
    sendResponse({ success: true })
  }
})
