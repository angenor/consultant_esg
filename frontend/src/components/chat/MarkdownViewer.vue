<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Viewer from '@toast-ui/editor/dist/toastui-editor-viewer'
import codeSyntaxHighlight from '@toast-ui/editor-plugin-code-syntax-highlight'
import tableMergedCell from '@toast-ui/editor-plugin-table-merged-cell'
import chart from '@toast-ui/editor-plugin-chart'
import Prism from 'prismjs'
import mermaid from 'mermaid'

import '@toast-ui/editor/dist/toastui-editor-viewer.css'
import '@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css'
import '@toast-ui/editor-plugin-table-merged-cell/dist/toastui-editor-plugin-table-merged-cell.css'
import '@toast-ui/chart/dist/toastui-chart.css'

// Initialize Mermaid with a theme that matches the app
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'sans-serif',
  flowchart: {
    padding: 20,
    useMaxWidth: false,
  },
  sequence: {
    useMaxWidth: false,
  },
})

let mermaidIdCounter = 0

// Custom TOAST UI plugin: renders ```mermaid code blocks as diagrams
function mermaidPlugin() {
  return {
    toHTMLRenderers: {
      codeBlock(node: any) {
        if (node.info === 'mermaid') {
          const id = `mermaid-${Date.now()}-${mermaidIdCounter++}`
          return [
            { type: 'openTag', tagName: 'div', classNames: ['mermaid-container'] },
            { type: 'openTag', tagName: 'pre', classNames: ['mermaid'], attributes: { id } },
            { type: 'text', content: node.literal || '' },
            { type: 'closeTag', tagName: 'pre' },
            { type: 'closeTag', tagName: 'div' },
          ]
        }
        return null
      },
    },
  }
}

// Render all .mermaid elements inside the container
async function renderMermaidDiagrams() {
  if (!containerRef.value) return
  const els = containerRef.value.querySelectorAll<HTMLElement>('pre.mermaid:not([data-mermaid-rendered])')
  if (els.length === 0) return

  for (const el of els) {
    try {
      const code = el.textContent || ''
      const id = el.id || `mermaid-${Date.now()}-${mermaidIdCounter++}`
      const { svg } = await mermaid.render(id + '-svg', code)
      el.innerHTML = svg
      el.setAttribute('data-mermaid-rendered', 'true')
    } catch {
      el.innerHTML = '<p class="text-red-500 text-sm">Erreur de rendu du diagramme Mermaid</p>'
      el.setAttribute('data-mermaid-rendered', 'true')
    }
  }
}

const props = defineProps<{
  content: string
  isStreaming?: boolean
}>()

const containerRef = ref<HTMLElement>()
const modalOpen = ref(false)
const modalHtml = ref('')
let viewer: Viewer | null = null
let throttleTimer: ReturnType<typeof setTimeout> | null = null
let retryTimer: ReturnType<typeof setTimeout> | null = null
let lastRendered = ''

function hasChartBlocks(md: string): boolean {
  return /\$\$chart\n[\s\S]*?\n\$\$/.test(md)
}

const chartPluginOptions = { width: 560, height: 320, minWidth: 300, minHeight: 200, maxWidth: 900, maxHeight: 500 }

function destroyViewer() {
  if (viewer) {
    viewer.destroy()
    viewer = null
  }
  // Also clear the container DOM to avoid stale chart state
  if (containerRef.value) {
    containerRef.value.innerHTML = ''
  }
}

function createViewer(content?: string) {
  if (!containerRef.value) return
  viewer = new Viewer({
    el: containerRef.value,
    initialValue: content || '',
    plugins: [
      [codeSyntaxHighlight, { highlighter: Prism }],
      tableMergedCell,
      [chart, chartPluginOptions],
      mermaidPlugin,
    ],
    usageStatistics: false,
  })
  lastRendered = content || ''
}

// Retry chart rendering until all charts have canvases.
// The chart plugin sometimes fails to create canvases on first try.
function ensureCharts(content: string, attempt = 0) {
  const delays = [200, 500, 1000]
  const delay = delays[attempt] ?? 1000

  retryTimer = setTimeout(() => {
    retryTimer = null
    if (!containerRef.value) return

    const chartEls = containerRef.value.querySelectorAll('[data-chart-id]')
    const canvases = containerRef.value.querySelectorAll('canvas')

    if (chartEls.length > 0 && canvases.length < chartEls.length && attempt < delays.length) {
      // Some charts failed — destroy everything and recreate from scratch
      destroyViewer()
      createViewer(content)
      nextTick(() => {
        wrapTables()
        ensureCharts(content, attempt + 1)
      })
    } else {
      // All charts rendered or max retries reached — wrap tables + render mermaid
      nextTick(() => {
        wrapTables()
        renderMermaidDiagrams()
      })
    }
  }, delay)
}

function createExpandButton(targetWrapper: HTMLElement) {
  const btn = document.createElement('button')
  btn.className = 'expand-btn'
  btn.title = 'Agrandir'
  btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>'
  btn.addEventListener('click', (e) => {
    e.stopPropagation()
    openModal(targetWrapper)
  })
  return btn
}

function openModal(wrapper: HTMLElement) {
  const clone = wrapper.cloneNode(true) as HTMLElement
  // Convert canvas elements to images (for charts)
  const origCanvases = wrapper.querySelectorAll('canvas')
  const clonedCanvases = clone.querySelectorAll('canvas')
  clonedCanvases.forEach((canvas, i) => {
    const orig = origCanvases[i]
    if (!orig) return
    try {
      const img = document.createElement('img')
      img.src = orig.toDataURL()
      // No fixed dimensions — let CSS scale them up in the modal
      canvas.replaceWith(img)
    } catch { /* ignore cross-origin */ }
  })
  // Remove expand buttons from cloned content
  clone.querySelectorAll('.expand-btn').forEach((b) => b.remove())
  // Remove scroll-wrapper classes so content isn't constrained
  clone.classList.remove('table-scroll-wrapper', 'chart-scroll-wrapper')
  modalHtml.value = clone.innerHTML
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  modalHtml.value = ''
}

function wrapTables() {
  if (!containerRef.value) return
  const tables = containerRef.value.querySelectorAll(
    '.toastui-editor-contents > table:not(.table-wrapped)'
  )
  tables.forEach((table) => {
    table.classList.add('table-wrapped')
    const wrapper = document.createElement('div')
    wrapper.className = 'table-scroll-wrapper'
    table.parentNode!.insertBefore(wrapper, table)
    wrapper.appendChild(table)
    wrapper.appendChild(createExpandButton(wrapper))
  })
  // Wrap chart elements in scrollable containers
  const charts = containerRef.value.querySelectorAll(
    '.toastui-editor-contents > [data-chart-id]:not(.chart-wrapped)'
  )
  charts.forEach((chart) => {
    chart.classList.add('chart-wrapped')
    const wrapper = document.createElement('div')
    wrapper.className = 'chart-scroll-wrapper'
    chart.parentNode!.insertBefore(wrapper, chart)
    wrapper.appendChild(chart)
    wrapper.appendChild(createExpandButton(wrapper))
  })
  // Add expand buttons to mermaid containers
  const mermaids = containerRef.value.querySelectorAll(
    '.mermaid-container:not(.mermaid-expandable)'
  )
  mermaids.forEach((container) => {
    container.classList.add('mermaid-expandable')
    ;(container as HTMLElement).style.position = 'relative'
    container.appendChild(createExpandButton(container as HTMLElement))
  })
}

// During streaming, replace $$chart blocks with a placeholder to avoid
// repeated chart creation/destruction which causes flickering.
// Complete blocks ($$chart...$$) are replaced by a text placeholder.
// Incomplete blocks ($$chart without closing $$) are shown as-is.
function hasMermaidBlocks(md: string): boolean {
  return /```mermaid\n[\s\S]*?\n```/.test(md)
}

function sanitizeForStreaming(markdown: string): string {
  // Replace complete $$chart...$ blocks with a placeholder
  let result = markdown.replace(
    /\$\$chart\n[\s\S]*?\n\$\$/g,
    '\n> *Graphique en cours de chargement...*\n'
  )
  // If there's an incomplete $$chart block (opened but not closed), show placeholder
  const lastOpen = result.lastIndexOf('$$chart')
  if (lastOpen !== -1) {
    const afterOpen = result.indexOf('\n$$', lastOpen + 7)
    if (afterOpen === -1) {
      // Incomplete block — truncate it and show placeholder
      result = result.substring(0, lastOpen) + '\n> *Graphique en cours de chargement...*'
    }
  }
  // Replace complete ```mermaid...``` blocks with a placeholder during streaming
  result = result.replace(
    /```mermaid\n[\s\S]*?\n```/g,
    '\n> *Diagramme en cours de chargement...*\n'
  )
  // If there's an incomplete ```mermaid block (opened but not closed), show placeholder
  const lastMermaidOpen = result.lastIndexOf('```mermaid')
  if (lastMermaidOpen !== -1) {
    const afterMermaid = result.indexOf('\n```', lastMermaidOpen + 10)
    if (afterMermaid === -1) {
      result = result.substring(0, lastMermaidOpen) + '\n> *Diagramme en cours de chargement...*'
    }
  }
  return result
}

function updateContent(markdown: string, streaming = false) {
  if (!viewer || markdown === lastRendered) return
  const toRender = streaming ? sanitizeForStreaming(markdown) : markdown
  viewer.setMarkdown(toRender)
  lastRendered = markdown
  nextTick(() => {
    wrapTables()
    if (!streaming && hasMermaidBlocks(markdown)) {
      renderMermaidDiagrams()
    }
  })
}

// Throttled update during streaming to avoid excessive re-renders
function throttledUpdate(markdown: string) {
  if (props.isStreaming) {
    if (!throttleTimer) {
      throttleTimer = setTimeout(() => {
        throttleTimer = null
        updateContent(markdown, true)
      }, 120)
    }
  } else {
    // Final render immediately when streaming ends
    if (throttleTimer) {
      clearTimeout(throttleTimer)
      throttleTimer = null
    }
    updateContent(markdown, false)
  }
}

watch(() => props.content, (newVal) => {
  throttledUpdate(newVal)
})

// When streaming ends, force a final re-render (charts need this)
watch(() => props.isStreaming, (streaming) => {
  if (!streaming) {
    lastRendered = '' // Force re-render even if content matches
    nextTick(() => updateContent(props.content, false))
  }
})

onMounted(() => {
  const content = props.content || ''
  if (hasChartBlocks(content) && !props.isStreaming) {
    // For content with $$chart blocks: create viewer with empty content first
    // to let the DOM lay out, then destroy & recreate with chart content.
    createViewer('')
    retryTimer = setTimeout(() => {
      retryTimer = null
      destroyViewer()
      createViewer(content)
      nextTick(() => {
        wrapTables()
        // Start checking if charts need retrying
        ensureCharts(content, 0)
      })
    }, 100)
  } else {
    createViewer(content)
    nextTick(() => {
      wrapTables()
      if (hasMermaidBlocks(content)) {
        renderMermaidDiagrams()
      }
    })
  }
})

onBeforeUnmount(() => {
  if (throttleTimer) clearTimeout(throttleTimer)
  if (retryTimer) clearTimeout(retryTimer)
  destroyViewer()
})
</script>

<template>
  <div class="markdown-viewer-wrapper">
    <div ref="containerRef" class="tui-viewer-content" />
    <span
      v-if="isStreaming"
      class="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-emerald-400"
    />

    <!-- Fullscreen modal -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="modalOpen"
          class="expand-modal-overlay"
          @click.self="closeModal"
        >
          <Transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="scale-95 opacity-0"
            enter-to-class="scale-100 opacity-100"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="scale-100 opacity-100"
            leave-to-class="scale-95 opacity-0"
            appear
          >
            <div class="expand-modal-content">
              <button class="expand-modal-close" @click="closeModal">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
              <div class="expand-modal-body toastui-editor-contents" v-html="modalHtml" />
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style>
/* ── TUI Viewer overrides to blend with chat bubbles ── */
.markdown-viewer-wrapper {
  min-width: 0;
  overflow: hidden;
}

.tui-viewer-content {
  min-width: 0;
}

.tui-viewer-content .toastui-editor-contents {
  font-size: 0.875rem;
  line-height: 1.625;
  color: inherit;
  font-family: inherit;
  min-width: 0;
}

.tui-viewer-content .toastui-editor-contents p {
  margin: 0 0 0.5em;
  color: inherit;
}

.tui-viewer-content .toastui-editor-contents p:last-child {
  margin-bottom: 0;
}

.tui-viewer-content .toastui-editor-contents h1,
.tui-viewer-content .toastui-editor-contents h2,
.tui-viewer-content .toastui-editor-contents h3,
.tui-viewer-content .toastui-editor-contents h4 {
  margin: 0.75em 0 0.4em;
  padding-bottom: 0;
  border-bottom: none;
  color: inherit;
  font-weight: 700;
}

.tui-viewer-content .toastui-editor-contents h1:first-child,
.tui-viewer-content .toastui-editor-contents h2:first-child,
.tui-viewer-content .toastui-editor-contents h3:first-child {
  margin-top: 0;
}

.tui-viewer-content .toastui-editor-contents h1 { font-size: 1.25rem; }
.tui-viewer-content .toastui-editor-contents h2 { font-size: 1.125rem; }
.tui-viewer-content .toastui-editor-contents h3 { font-size: 1rem; }
.tui-viewer-content .toastui-editor-contents h4 { font-size: 0.9375rem; }

.tui-viewer-content .toastui-editor-contents ul,
.tui-viewer-content .toastui-editor-contents ol {
  margin: 0.4em 0;
  padding-left: 1.5em;
}

.tui-viewer-content .toastui-editor-contents li {
  margin: 0.15em 0;
}

.tui-viewer-content .toastui-editor-contents ul > li {
  list-style-type: disc;
}

.tui-viewer-content .toastui-editor-contents ol > li {
  list-style-type: decimal;
}

/* Task list (checkboxes) */
.tui-viewer-content .toastui-editor-contents .task-list-item {
  list-style-type: none;
  margin-left: -1.25em;
}

/* Expand button on wrappers */
.table-scroll-wrapper,
.chart-scroll-wrapper,
.mermaid-container {
  position: relative;
}

.expand-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.85);
  color: #6b7280;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
  backdrop-filter: blur(4px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.table-scroll-wrapper:hover .expand-btn,
.chart-scroll-wrapper:hover .expand-btn,
.mermaid-container:hover .expand-btn {
  opacity: 1;
}

.expand-btn:hover {
  background: #059669;
  color: #ffffff;
}

/* Fullscreen modal */
.expand-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  padding: 1.5rem;
}

.expand-modal-content {
  position: relative;
  width: 90vw;
  max-width: 1200px;
  max-height: 90vh;
  background: #ffffff;
  border-radius: 1rem;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  overflow: auto;
  padding: 2rem;
}

.expand-modal-close {
  position: sticky;
  top: 0;
  float: right;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: #f3f4f6;
  color: #6b7280;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  margin-left: auto;
}

.expand-modal-close:hover {
  background: #ef4444;
  color: #ffffff;
}

.expand-modal-body {
  font-size: 1rem;
  line-height: 1.7;
  color: #1f2937;
}

/* Tables in modal — full width */
.expand-modal-body table {
  border-collapse: collapse;
  font-size: 0.9375rem;
  width: 100%;
}

.expand-modal-body th {
  background-color: #059669 !important;
  color: #ffffff !important;
  font-weight: 600;
  text-align: left;
  padding: 0.75em 1.25em;
  border: 1px solid #047857;
}

.expand-modal-body td {
  padding: 0.65em 1.25em;
  border: 1px solid #e5e7eb;
  color: #1f2937 !important;
  background-color: #ffffff !important;
}

.expand-modal-body tr:nth-child(even) td {
  background-color: #f9fafb !important;
}

/* Charts/images in modal — scale up to fill */
.expand-modal-body img {
  width: 100%;
  height: auto;
  display: block;
}

.expand-modal-body canvas {
  width: 100%;
  height: auto;
}

/* Mermaid SVGs in modal */
.expand-modal-body svg {
  width: 100%;
  height: auto;
  display: block;
}

/* Remove nested scroll constraints inside modal */
.expand-modal-body .toastui-chart-wrapper {
  width: 100% !important;
  height: auto !important;
}

/* Tables — horizontal scroll wrapper */
.tui-viewer-content .table-scroll-wrapper {
  overflow-x: auto;
  margin: 0.75em -0.5em;
  padding: 0 0.5em;
  -webkit-overflow-scrolling: touch;
}

.tui-viewer-content .table-scroll-wrapper::-webkit-scrollbar {
  height: 4px;
}

.tui-viewer-content .table-scroll-wrapper::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.tui-viewer-content .toastui-editor-contents table {
  border-collapse: collapse;
  font-size: 0.8125rem;
  width: max-content;
  min-width: 100%;
}

.tui-viewer-content .toastui-editor-contents th {
  background-color: #059669 !important;
  color: #ffffff !important;
  font-weight: 600;
  text-align: left;
  padding: 0.5em 0.75em;
  border: 1px solid #047857;
  white-space: nowrap;
}

.tui-viewer-content .toastui-editor-contents td {
  padding: 0.4em 0.75em;
  border: 1px solid #e5e7eb;
  color: #1f2937 !important;
  background-color: #ffffff !important;
}

.tui-viewer-content .toastui-editor-contents tr:nth-child(even) td {
  background-color: #f9fafb !important;
}

/* Code blocks */
.tui-viewer-content .toastui-editor-contents pre {
  background-color: #1e293b;
  color: #e2e8f0;
  border-radius: 0.5rem;
  padding: 0.75em 1em;
  margin: 0.5em 0;
  overflow-x: auto;
  font-size: 0.8125rem;
}

.tui-viewer-content .toastui-editor-contents pre code {
  background: none;
  padding: 0;
  color: inherit;
  font-size: inherit;
}

/* Inline code */
.tui-viewer-content .toastui-editor-contents code {
  background-color: rgba(5, 150, 105, 0.1);
  color: #059669;
  padding: 0.15em 0.35em;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
}

/* Blockquotes */
.tui-viewer-content .toastui-editor-contents blockquote {
  margin: 0.5em 0;
  padding: 0.25em 0 0.25em 1em;
  border-left: 3px solid #059669;
  color: inherit;
  opacity: 0.85;
}

.tui-viewer-content .toastui-editor-contents blockquote p {
  margin: 0;
}

/* Horizontal rule */
.tui-viewer-content .toastui-editor-contents hr {
  margin: 0.75em 0;
  border-color: #e5e7eb;
}

/* Bold/strong */
.tui-viewer-content .toastui-editor-contents strong {
  font-weight: 700;
  color: inherit;
}

/* Links */
.tui-viewer-content .toastui-editor-contents a {
  color: #059669;
  text-decoration: underline;
  text-underline-offset: 2px;
}

/* Charts — horizontal scroll wrapper */
.tui-viewer-content .chart-scroll-wrapper {
  overflow-x: auto;
  margin: 0.75em -0.5em;
  padding: 0 0.5em;
  -webkit-overflow-scrolling: touch;
}

.tui-viewer-content .chart-scroll-wrapper::-webkit-scrollbar {
  height: 4px;
}

.tui-viewer-content .chart-scroll-wrapper::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.tui-viewer-content .toastui-editor-contents [data-chart-id] {
  min-height: 320px;
  border-radius: 0.5rem;
  overflow: visible;
  min-width: max-content;
}

.tui-viewer-content .toastui-editor-contents .toastui-chart-wrapper {
  min-height: 320px;
}

.tui-viewer-content .toastui-editor-contents canvas {
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
}

/* Mermaid diagrams */
.tui-viewer-content .mermaid-container {
  margin: 0.75em 0;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.tui-viewer-content .toastui-editor-contents pre.mermaid {
  background-color: #ffffff;
  color: #1f2937;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 0.5em 0;
  text-align: center;
  overflow-x: auto;
}

.tui-viewer-content .toastui-editor-contents pre.mermaid svg {
  max-width: 100%;
  height: auto;
  display: block;
}
</style>
