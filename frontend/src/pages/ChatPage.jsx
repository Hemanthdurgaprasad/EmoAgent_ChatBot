import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../api/client'

function renderContent(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^• /gm, '&bull; ')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>')
}

export default function ChatPage() {
  const { user, logout } = useAuth()
  const [sessions, setSessions] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => { loadSessions() }, [])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function loadSessions() {
    try {
      const data = await api.history.getSessions()
      setSessions(data)
    } catch { /* token expired handled by app */ }
  }

  async function openSession(id) {
    if (streaming) return
    try {
      const data = await api.history.getSession(id)
      setActiveId(id)
      setMessages(data.messages.map(m => ({ ...m, id: Math.random() })))
    } catch { }
  }

  function newChat() {
    if (streaming) return
    setActiveId(null)
    setMessages([])
    setInput('')
    inputRef.current?.focus()
  }

  async function deleteSession(e, id) {
    e.stopPropagation()
    await api.history.deleteSession(id)
    setSessions(s => s.filter(x => x.id !== id))
    if (activeId === id) newChat()
  }

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || streaming) return

    const userMsg = { id: Math.random(), role: 'user', content: text }
    setMessages(m => [...m, userMsg])
    setInput('')
    setStreaming(true)

    const assistantMsg = { id: Math.random(), role: 'assistant', content: '' }
    setMessages(m => [...m, assistantMsg])

    let currentSessionId = activeId
    let sessionConfirmed = false

    const controller = await api.chat.stream(
      text,
      activeId,
      (token) => {
        setMessages(m => {
          const copy = [...m]
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            content: copy[copy.length - 1].content + token
          }
          return copy
        })
      },
      (sid, isSessionId) => {
        if (isSessionId && !sessionConfirmed) {
          currentSessionId = sid
          setActiveId(sid)
          sessionConfirmed = true
        } else {
          setStreaming(false)
          loadSessions()
        }
      },
      (err) => {
        setMessages(m => {
          const copy = [...m]
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            content: 'Something went wrong. Please try again.',
            error: true
          }
          return copy
        })
        setStreaming(false)
      }
    )
    abortRef.current = controller
  }, [input, streaming, activeId])

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const isEmpty = messages.length === 0

  return (
    <div style={s.shell}>
      {/* Sidebar */}
      <aside style={{ ...s.sidebar, transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)' }}>
        <div style={s.sideTop}>
          <div style={s.brand}>
            <div style={s.brandDot} />
            <span style={s.brandName}>EmoAgent</span>
          </div>
          <button style={s.newBtn} onClick={newChat}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 1v12M1 7h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            New chat
          </button>
        </div>

        <div style={s.sessionList}>
          {sessions.length === 0 && (
            <p style={s.emptyHistory}>No conversations yet</p>
          )}
          {sessions.map(sess => (
            <div
              key={sess.id}
              style={{ ...s.sessionItem, ...(activeId === sess.id ? s.sessionActive : {}) }}
              onClick={() => openSession(sess.id)}
            >
              <div style={s.sessionTitle}>{sess.title}</div>
              <div style={s.sessionMeta}>{sess.message_count} messages</div>
              <button
                style={s.deleteBtn}
                onClick={e => deleteSession(e, sess.id)}
                title="Delete"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </button>
            </div>
          ))}
        </div>

        <div style={s.sideBottom}>
          <div style={s.userRow}>
            <div style={s.avatar}>{user?.name?.[0]?.toUpperCase()}</div>
            <div>
              <div style={s.userName}>{user?.name}</div>
              <div style={s.userEmail}>{user?.email}</div>
            </div>
          </div>
          <button style={s.logoutBtn} onClick={logout}>Sign out</button>
        </div>
      </aside>

      {/* Main */}
      <main style={s.main}>
        {/* Topbar */}
        <header style={s.topbar}>
          <button style={s.menuBtn} onClick={() => setSidebarOpen(o => !o)}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M2 4h14M2 9h14M2 14h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </button>
          <span style={s.topbarTitle}>
            {activeId ? sessions.find(s => s.id === activeId)?.title || 'Chat' : 'New conversation'}
          </span>
          <div style={{ width: 36 }} />
        </header>

        {/* Messages */}
        <div style={s.messageArea}>
          {isEmpty && <EmptyState name={user?.name} />}
          {messages.map(msg => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={s.inputWrap}>
          <div style={s.inputRow}>
            <textarea
              ref={inputRef}
              style={s.textarea}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Share what's on your mind…"
              rows={1}
              disabled={streaming}
            />
            <button
              style={{ ...s.sendBtn, opacity: (input.trim() && !streaming) ? 1 : 0.4 }}
              onClick={send}
              disabled={!input.trim() || streaming}
            >
              {streaming
                ? <span style={s.stopDot} onClick={() => abortRef.current?.abort()} />
                : <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M2 8h12M8 2l6 6-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
              }
            </button>
          </div>
          <p style={s.inputHint}>EmoAgent is a wellness companion, not a therapist. In crisis, call iCall: 9152987821</p>
        </div>
      </main>
    </div>
  )
}

function EmptyState({ name }) {
  const prompts = [
    "I've been feeling overwhelmed lately…",
    "I'm struggling to find motivation",
    "I need to talk about my anxiety",
    "I had a really hard day today",
  ]
  return (
    <div style={s.empty}>
      <div style={s.emptyIcon}>
        <div style={s.emptyIconInner} />
      </div>
      <h2 style={s.emptyHeading}>Hello, {name?.split(' ')[0]} 👋</h2>
      <p style={s.emptySub}>How are you feeling today? I'm here to listen.</p>
      <div style={s.promptGrid}>
        {prompts.map(p => (
          <div key={p} style={s.promptChip}
            onClick={() => {
              const ta = document.querySelector('textarea')
              if (ta) { ta.value = p; ta.dispatchEvent(new Event('input', { bubbles: true })) }
            }}
          >{p}</div>
        ))}
      </div>
    </div>
  )
}

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{ ...s.bubbleRow, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      {!isUser && <div style={s.agentAvatar} />}
      <div style={{
        ...s.bubble,
        ...(isUser ? s.bubbleUser : s.bubbleAgent),
        ...(msg.error ? s.bubbleError : {})
      }}>
        {isUser
          ? <p style={{ lineHeight: 1.6 }}>{msg.content}</p>
          : <div
              className="prose"
              dangerouslySetInnerHTML={{ __html: `<p>${renderContent(msg.content) || '<span style="opacity:0.4">…</span>'}</p>` }}
            />
        }
      </div>
    </div>
  )
}

const s = {
  shell: { display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--warm)' },

  // Sidebar
  sidebar: {
    width: 260, minWidth: 260, height: '100vh',
    background: 'var(--white)',
    borderRight: '1px solid var(--warm-mid)',
    display: 'flex', flexDirection: 'column',
    transition: 'transform 0.25s ease',
    position: 'relative', zIndex: 10,
  },
  sideTop: { padding: '1.25rem 1rem 1rem' },
  brand: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1rem' },
  brandDot: { width: 20, height: 20, borderRadius: '50%', background: 'var(--sage)' },
  brandName: { fontFamily: "'DM Serif Display', serif", fontSize: 17, color: 'var(--ink)' },
  newBtn: {
    width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
    gap: 6, padding: '8px 12px',
    background: 'var(--sage-light)', color: 'var(--sage)',
    border: '1px solid var(--sage-mid)', borderRadius: 'var(--radius-sm)',
    fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit',
  },
  sessionList: { flex: 1, overflowY: 'auto', padding: '0 0.5rem' },
  emptyHistory: { fontSize: 13, color: 'var(--ink-soft)', textAlign: 'center', padding: '1.5rem 1rem' },
  sessionItem: {
    padding: '10px 10px', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
    marginBottom: 2, position: 'relative',
    transition: 'background 0.1s',
  },
  sessionActive: { background: 'var(--sage-light)' },
  sessionTitle: { fontSize: 13, fontWeight: 500, color: 'var(--ink)', marginBottom: 2, paddingRight: 20, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  sessionMeta: { fontSize: 11, color: 'var(--ink-soft)' },
  deleteBtn: {
    position: 'absolute', top: 10, right: 8,
    background: 'none', border: 'none', cursor: 'pointer',
    color: 'var(--ink-soft)', padding: 2, borderRadius: 4, opacity: 0.6,
  },
  sideBottom: { padding: '1rem', borderTop: '1px solid var(--warm-mid)' },
  userRow: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: '0.75rem' },
  avatar: {
    width: 32, height: 32, borderRadius: '50%',
    background: 'var(--sage)', color: 'var(--white)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 13, fontWeight: 500, flexShrink: 0,
  },
  userName: { fontSize: 13, fontWeight: 500, color: 'var(--ink)' },
  userEmail: { fontSize: 11, color: 'var(--ink-soft)' },
  logoutBtn: {
    width: '100%', padding: '7px', background: 'none',
    border: '1px solid var(--warm-mid)', borderRadius: 'var(--radius-sm)',
    fontSize: 13, color: 'var(--ink-mid)', cursor: 'pointer', fontFamily: 'inherit',
  },

  // Main
  main: { flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' },
  topbar: {
    height: 54, borderBottom: '1px solid var(--warm-mid)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '0 1rem', background: 'var(--white)', flexShrink: 0,
  },
  menuBtn: { width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink-mid)', borderRadius: 'var(--radius-sm)' },
  topbarTitle: { fontSize: 14, fontWeight: 500, color: 'var(--ink)', flex: 1, textAlign: 'center', paddingInline: 8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },

  // Messages
  messageArea: { flex: 1, overflowY: 'auto', padding: '1.5rem 1rem', display: 'flex', flexDirection: 'column', gap: '1rem' },

  // Empty state
  empty: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '2rem', marginTop: '4rem' },
  emptyIcon: { width: 56, height: 56, borderRadius: '50%', background: 'var(--sage-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.25rem' },
  emptyIconInner: { width: 24, height: 24, borderRadius: '50%', background: 'var(--sage)' },
  emptyHeading: { fontFamily: "'DM Serif Display', serif", fontSize: 26, fontWeight: 400, color: 'var(--ink)', marginBottom: '0.5rem' },
  emptySub: { fontSize: 15, color: 'var(--ink-soft)', marginBottom: '1.75rem' },
  promptGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, maxWidth: 460, width: '100%' },
  promptChip: {
    padding: '10px 14px', background: 'var(--white)', border: '1px solid var(--warm-mid)',
    borderRadius: 'var(--radius-sm)', fontSize: 13, color: 'var(--ink-mid)',
    cursor: 'pointer', textAlign: 'left', lineHeight: 1.4,
    transition: 'border-color 0.15s, background 0.15s',
  },

  // Bubbles
  bubbleRow: { display: 'flex', alignItems: 'flex-end', gap: 10 },
  agentAvatar: { width: 28, height: 28, borderRadius: '50%', background: 'var(--sage)', flexShrink: 0 },
  bubble: { maxWidth: '72%', padding: '12px 16px', borderRadius: 16, lineHeight: 1.65, fontSize: 15 },
  bubbleUser: { background: 'var(--sage)', color: 'var(--white)', borderBottomRightRadius: 4 },
  bubbleAgent: { background: 'var(--white)', color: 'var(--ink)', border: '1px solid var(--warm-mid)', borderBottomLeftRadius: 4 },
  bubbleError: { background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid #f5c6c2' },

  // Input
  inputWrap: { padding: '0.75rem 1rem 1rem', background: 'var(--white)', borderTop: '1px solid var(--warm-mid)', flexShrink: 0 },
  inputRow: { display: 'flex', alignItems: 'flex-end', gap: 8, background: 'var(--warm)', border: '1.5px solid var(--warm-mid)', borderRadius: 14, padding: '8px 8px 8px 14px' },
  textarea: {
    flex: 1, background: 'none', border: 'none', outline: 'none', resize: 'none',
    fontSize: 15, fontFamily: 'inherit', color: 'var(--ink)', lineHeight: 1.6,
    maxHeight: 140, overflowY: 'auto',
  },
  sendBtn: {
    width: 36, height: 36, borderRadius: 10, background: 'var(--sage)',
    border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center',
    justifyContent: 'center', color: 'var(--white)', flexShrink: 0, transition: 'opacity 0.15s',
  },
  stopDot: { width: 10, height: 10, borderRadius: 2, background: 'var(--white)' },
  inputHint: { fontSize: 11, color: 'var(--ink-soft)', textAlign: 'center', marginTop: 6 },
}
