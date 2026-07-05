import { useState, useCallback } from 'react'
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  VoiceAssistantControlBar,
} from '@livekit/components-react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

function CallUI() {
  const { state, audioTrack } = useVoiceAssistant()
  return (
    <div style={{ textAlign: 'center', padding: '2rem' }}>
      <p style={{ opacity: 0.7 }}>Status: {state}</p>
      <BarVisualizer state={state} trackRef={audioTrack} barCount={7} style={{ height: 80 }} />
      <VoiceAssistantControlBar />
      <RoomAudioRenderer />
    </div>
  )
}

export default function App() {
  const [connectionDetails, setConnectionDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const startCall = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BACKEND_URL}/livekit-token?name=patient`)
      if (!res.ok) throw new Error('Could not get a call token from the server.')
      const data = await res.json()
      setConnectionDetails(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  if (!connectionDetails) {
    return (
      <div style={{ maxWidth: 480, margin: '4rem auto', textAlign: 'center', fontFamily: 'sans-serif' }}>
        <h1>City Care Clinic</h1>
        <p>Talk to our voice assistant to book, check, reschedule, or cancel an appointment.</p>
        <button
          onClick={startCall}
          disabled={loading}
          style={{
            padding: '0.9rem 2rem',
            fontSize: '1.1rem',
            borderRadius: 999,
            border: 'none',
            background: '#2563eb',
            color: 'white',
            cursor: 'pointer',
          }}
        >
          {loading ? 'Connecting…' : '🎙️ Start Call'}
        </button>
        {error && <p style={{ color: 'crimson' }}>{error}</p>}
      </div>
    )
  }

  return (
    <LiveKitRoom
      serverUrl={connectionDetails.url}
      token={connectionDetails.token}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={() => setConnectionDetails(null)}
      style={{ height: '100vh' }}
    >
      <CallUI />
    </LiveKitRoom>
  )
}
