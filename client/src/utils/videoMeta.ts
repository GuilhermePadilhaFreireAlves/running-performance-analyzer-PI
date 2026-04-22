import type { VideoMetadata } from './videoValidation'

const FPS_SAMPLE_DURATION_SEC = 0.6
const FPS_SAMPLE_TIMEOUT_MS = 2000

function hasFrameCallback(video: HTMLVideoElement): boolean {
  return (
    'requestVideoFrameCallback' in video &&
    typeof video.requestVideoFrameCallback === 'function'
  )
}

function estimateFps(video: HTMLVideoElement): Promise<number | null> {
  return new Promise((resolve) => {
    if (!hasFrameCallback(video)) {
      resolve(null)
      return
    }
    let firstMediaTime: number | null = null
    let lastMediaTime: number | null = null
    let frameCount = 0
    let done = false

    const finish = (): void => {
      if (done) return
      done = true
      try {
        video.pause()
      } catch {
        // ignore
      }
      if (
        firstMediaTime !== null &&
        lastMediaTime !== null &&
        frameCount > 1 &&
        lastMediaTime > firstMediaTime
      ) {
        resolve((frameCount - 1) / (lastMediaTime - firstMediaTime))
      } else {
        resolve(null)
      }
    }

    const onFrame: VideoFrameRequestCallback = (_now, metadata) => {
      if (done) return
      if (firstMediaTime === null) {
        firstMediaTime = metadata.mediaTime
      }
      lastMediaTime = metadata.mediaTime
      frameCount += 1
      if (
        firstMediaTime !== null &&
        lastMediaTime - firstMediaTime >= FPS_SAMPLE_DURATION_SEC
      ) {
        finish()
        return
      }
      video.requestVideoFrameCallback(onFrame)
    }

    setTimeout(finish, FPS_SAMPLE_TIMEOUT_MS)
    video.requestVideoFrameCallback(onFrame)
    video.play().catch(() => finish())
  })
}

export const READ_METADATA_ERROR =
  'Não foi possível ler metadados do vídeo. Verifique o arquivo e tente novamente.'

export function readVideoMetadata(file: File): Promise<VideoMetadata> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const video = document.createElement('video')
    video.preload = 'auto'
    video.muted = true
    video.playsInline = true

    const cleanup = (): void => {
      URL.revokeObjectURL(url)
      video.removeAttribute('src')
      try {
        video.load()
      } catch {
        // ignore
      }
    }

    video.addEventListener('loadedmetadata', () => {
      const baseMetadata: VideoMetadata = {
        durationSec: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
        estimatedFps: null,
      }
      estimateFps(video)
        .then((fps) => {
          cleanup()
          resolve({ ...baseMetadata, estimatedFps: fps })
        })
        .catch(() => {
          cleanup()
          resolve(baseMetadata)
        })
    })

    video.addEventListener('error', () => {
      cleanup()
      reject(new Error(READ_METADATA_ERROR))
    })

    video.src = url
  })
}
