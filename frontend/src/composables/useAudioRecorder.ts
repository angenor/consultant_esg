import { ref } from 'vue'

export type RecordingState = 'idle' | 'recording' | 'sending'

export function useAudioRecorder() {
  const state = ref<RecordingState>('idle')
  const error = ref<string | null>(null)

  let mediaRecorder: MediaRecorder | null = null
  let chunks: Blob[] = []
  let stream: MediaStream | null = null

  async function startRecording(): Promise<boolean> {
    error.value = null

    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        error.value = "Accès au microphone refusé. Veuillez autoriser l'accès dans les paramètres du navigateur."
      } else if (err instanceof DOMException && err.name === 'NotFoundError') {
        error.value = 'Aucun microphone détecté.'
      } else {
        error.value = "Impossible d'accéder au microphone."
      }
      return false
    }

    chunks = []

    // Choisir le format supporté par le navigateur
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : undefined // Laisser le navigateur choisir

    mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunks.push(e.data)
      }
    }

    mediaRecorder.start()
    state.value = 'recording'
    return true
  }

  function stopRecording(): Promise<Blob | null> {
    return new Promise((resolve) => {
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        state.value = 'idle'
        resolve(null)
        return
      }

      mediaRecorder.onstop = () => {
        const mimeType = mediaRecorder?.mimeType || 'audio/webm'
        const blob = new Blob(chunks, { type: mimeType })
        chunks = []

        // Libérer le microphone
        if (stream) {
          stream.getTracks().forEach((t) => t.stop())
          stream = null
        }

        mediaRecorder = null
        state.value = 'idle'
        resolve(blob)
      }

      mediaRecorder.stop()
    })
  }

  function cancelRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    chunks = []
    if (stream) {
      stream.getTracks().forEach((t) => t.stop())
      stream = null
    }
    mediaRecorder = null
    state.value = 'idle'
  }

  return {
    state,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  }
}
