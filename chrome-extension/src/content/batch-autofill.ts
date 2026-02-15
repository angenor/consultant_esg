/**
 * Remplit plusieurs champs d'un coup avec animation sequentielle
 */
export async function batchAutofill(
  mappings: Record<string, string>,
  options: { delay?: number; highlight?: boolean } = {}
): Promise<{ filled: number; failed: string[] }> {
  const { delay = 200, highlight = true } = options
  const failed: string[] = []
  let filled = 0

  for (const [selector, value] of Object.entries(mappings)) {
    const selectors = selector.split(',').map(s => s.trim())
    let element: HTMLElement | null = null

    for (const sel of selectors) {
      try {
        element = document.querySelector<HTMLElement>(sel)
        if (element) break
      } catch { /* continuer */ }
    }

    if (!element) {
      failed.push(selector)
      continue
    }

    if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
      element.focus()
      element.value = value
      element.dispatchEvent(new Event('input', { bubbles: true }))
      element.dispatchEvent(new Event('change', { bubbles: true }))

      if (highlight) {
        element.style.transition = 'background-color 0.3s, box-shadow 0.3s'
        element.style.backgroundColor = '#f0fdf4'
        element.style.boxShadow = '0 0 0 2px #059669'
        setTimeout(() => {
          element!.style.backgroundColor = ''
          element!.style.boxShadow = ''
        }, 1500)
      }

      filled++
    } else if (element instanceof HTMLSelectElement) {
      const option = Array.from(element.options).find(
        opt => opt.value === value || opt.text.toLowerCase().includes(value.toLowerCase())
      )
      if (option) {
        element.value = option.value
        element.dispatchEvent(new Event('change', { bubbles: true }))
        filled++
      } else {
        failed.push(selector)
      }
    }

    await new Promise(r => setTimeout(r, delay))
  }

  return { filled, failed }
}
