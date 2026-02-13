declare module '@toast-ui/editor/dist/toastui-editor-viewer' {
  import { Viewer } from '@toast-ui/editor'
  export default Viewer
}

declare module '@toast-ui/editor-plugin-code-syntax-highlight' {
  import type { PluginInfo } from '@toast-ui/editor'
  const plugin: PluginInfo
  export default plugin
}

declare module '@toast-ui/editor-plugin-table-merged-cell' {
  import type { PluginInfo } from '@toast-ui/editor'
  const plugin: PluginInfo
  export default plugin
}
