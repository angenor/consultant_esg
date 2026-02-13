<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Viewer from '@toast-ui/editor/dist/toastui-editor-viewer'
import codeSyntaxHighlight from '@toast-ui/editor-plugin-code-syntax-highlight'
import tableMergedCell from '@toast-ui/editor-plugin-table-merged-cell'
import chart from '@toast-ui/editor-plugin-chart'
import Prism from 'prismjs'

import '@toast-ui/editor/dist/toastui-editor-viewer.css'
import '@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css'
import '@toast-ui/editor-plugin-table-merged-cell/dist/toastui-editor-plugin-table-merged-cell.css'
import '@toast-ui/chart/dist/toastui-chart.css'

const props = defineProps<{
  content: string
  isStreaming?: boolean
}>()

const containerRef = ref<HTMLElement>()
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
      // All charts rendered or max retries reached — just wrap tables
      nextTick(wrapTables)
    }
  }, delay)
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
  })
}

// During streaming, replace $$chart blocks with a placeholder to avoid
// repeated chart creation/destruction which causes flickering.
// Complete blocks ($$chart...$$) are replaced by a text placeholder.
// Incomplete blocks ($$chart without closing $$) are shown as-is.
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
  return result
}

function updateContent(markdown: string, streaming = false) {
  if (!viewer || markdown === lastRendered) return
  const toRender = streaming ? sanitizeForStreaming(markdown) : markdown
  viewer.setMarkdown(toRender)
  lastRendered = markdown
  nextTick(wrapTables)
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
    nextTick(wrapTables)
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

/* Charts */
.tui-viewer-content .toastui-editor-contents [data-chart-id] {
  margin: 0.75em 0;
  min-height: 320px;
  border-radius: 0.5rem;
  overflow: hidden;
}

.tui-viewer-content .toastui-editor-contents .toastui-chart-wrapper {
  min-height: 320px;
}

.tui-viewer-content .toastui-editor-contents canvas {
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
}
</style>
