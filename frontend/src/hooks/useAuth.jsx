import { createContext, useContext, useState, useCallback } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('emoagent_user'))
    } catch { return null }
  })

  const login = useCallback(async (email, password) => {
    const data = await api.auth.login(email, password)
    localStorage.setItem('emoagent_token', data.access_token)
    localStorage.setItem('emoagent_user', JSON.stringify(data.user))
    setUser(data.user)
    return data.user
  }, [])

  const register = useCallback(async (name, email, password) => {
    const data = await api.auth.register(name, email, password)
    localStorage.setItem('emoagent_token', data.access_token)
    localStorage.setItem('emoagent_user', JSON.stringify(data.user))
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('emoagent_token')
    localStorage.removeItem('emoagent_user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
