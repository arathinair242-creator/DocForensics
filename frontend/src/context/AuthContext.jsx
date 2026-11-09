import { createContext, useContext, useState } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
  })

  const _persist = (data) => {
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data))
    setUser(data)
    return data
  }

  const login = async (email, password) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    const res = await api.post('/auth/login', form)
    return _persist(res.data)
  }

  const register = async (email, fullName, password) => {
    const res = await api.post('/auth/register', { email, full_name: fullName, password })
    return _persist(res.data)
  }

  const googleLogin = async (credential) => {
    const res = await fetch('http://localhost:8000/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Google login failed')
    _persist({ access_token: data.access_token, ...data })
    return data
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, googleLogin, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
