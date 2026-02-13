import { ref, onUnmounted } from 'vue'

export type RecordingState = 'idle' | 'recording' | 'sending'

export function useAudioRecorder() {
  const state = ref<RecordingState>('idle')
  const error = ref<string | null>(null)
  const audioLevel = ref(0) // 0-1, volume normalisé
  const elapsed = ref(0) // secondes écoulées

  let mediaRecorder: MediaRecorder | null = null
  let chunks: Blob[] = []
  let stream: MediaStream | null = null
  let analyser: AnalyserNode | null = null
  let audioCtx: AudioContext | null = null
  let animFrameId: number | null = null
  let timerInterval: ReturnType<typeof setInterval> | null = null

  function startLevelMonitoring() {
    if (!stream) return
    audioCtx = new AudioContext()
    const source = audioCtx.createMediaStreamSource(stream)
    analyser = audioCtx.createAnalyser()
    analyser.fftSize = 256
    analyser.smoothingTimeConstant = 0.5
    source.connect(analyser)

    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    function tick() {
      if (!analyser) return
      analyser.getByteFrequencyData(dataArray)
      // Moyenne des fréquences normalisée 0-1
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) sum += dataArray[i]!
      audioLevel.value = Math.min(sum / dataArray.length / 128, 1)
      animFrameId = requestAnimationFrame(tick)
    }
    tick()
  }

  function stopLevelMonitoring() {
    if (animFrameId !== null) {
      cancelAnimationFrame(animFrameId)
      animFrameId = null
    }
    if (audioCtx) {
      audioCtx.close()
      audioCtx = null
    }
    analyser = null
    audioLevel.value = 0
  }

  function startTimer() {
    elapsed.value = 0
    timerInterval = setInterval(() => {
      elapsed.value++
    }, 1000)
  }

  function stopTimer() {
    if (timerInterval !== null) {
      clearInterval(timerInterval)
      timerInterval = null
    }
    elapsed.value = 0
  }

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

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : undefined

    mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunks.push(e.data)
      }
    }

    mediaRecorder.start()
    state.value = 'recording'
    startLevelMonitoring()
    startTimer()
    return true
  }

  function stopRecording(): Promise<Blob | null> {
    return new Promise((resolve) => {
      stopLevelMonitoring()
      stopTimer()

      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        state.value = 'idle'
        resolve(null)
        return
      }

      mediaRecorder.onstop = () => {
        const mimeType = mediaRecorder?.mimeType || 'audio/webm'
        const blob = new Blob(chunks, { type: mimeType })
        chunks = []

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
    stopLevelMonitoring()
    stopTimer()
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

  onUnmounted(() => {
    cancelRecording()
  })

  return {
    state,
    error,
    audioLevel,
    elapsed,
    startRecording,
    stopRecording,
    cancelRecording,
  }
}
