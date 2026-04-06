const BASE = 'http://localhost:8000/api'

function getToken() {
  return localStorage.getItem('emoagent_token')
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  }
}

async function handleResponse(res) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  auth: {
    register: (name, email, password) =>
      fetch(`${BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      }).then(handleResponse),

    login: (email, password) =>
      fetch(`${BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      }).then(handleResponse),
  },

  history: {
    getSessions: () =>
      fetch(`${BASE}/history/sessions`, { headers: authHeaders() })
        .then(handleResponse),

    getSession: (id) =>
      fetch(`${BASE}/history/sessions/${id}`, { headers: authHeaders() })
        .then(handleResponse),

    deleteSession: (id) =>
      fetch(`${BASE}/history/sessions/${id}`, {
        method: 'DELETE',
        headers: authHeaders()
      }),
  },

  /**
   * Streams a chat response via SSE.
   * onToken(token) called for each streamed token.
   * onDone(sessionId) called when complete.
   * Returns a controller to abort mid-stream.
   */
  chat: {
    stream: async (message, sessionId, onToken, onDone, onError) => {
      const controller = new AbortController()
      try {
        const res = await fetch(`${BASE}/chat/stream`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ message, session_id: sessionId || null }),
          signal: controller.signal,
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: 'Stream failed' }))
          throw new Error(err.detail)
        }
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop()
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const event = JSON.parse(line.slice(6))
              if (event.type === 'token') onToken(event.token)
              else if (event.type === 'done') onDone(event.session_id)
              else if (event.type === 'session_id') onDone(event.session_id, true)
            } catch { /* skip malformed events */ }
          }
        }
      } catch (err) {
        if (err.name !== 'AbortError') onError?.(err.message)
      }
      return controller
    }
  }
}
