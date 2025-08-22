import React, { createContext, useContext, useEffect, useState } from 'react'
import { ConnectRequest, connect } from '@api/api'

interface AuthContextType {
  token: string | null
  role: 'admin' | 'user' | null
  login: (payload: ConnectRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  role: null,
  login: async () => {},
  logout: () => {},
})

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [role, setRole] = useState<'admin' | 'user' | null>(localStorage.getItem('role') as any)

  useEffect(() => {
    if (token) localStorage.setItem('token', token)
    else localStorage.removeItem('token')
  }, [token])

  useEffect(() => {
    if (role) localStorage.setItem('role', role)
    else localStorage.removeItem('role')
  }, [role])

  const login = async (payload: ConnectRequest) => {
    // Clear any existing auth data before attempting new connection
    setToken(null)
    setRole(null)
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    
    const { data } = await connect(payload)
    setToken(data.access_token)
    setRole(data.role)
  }

  const logout = () => {
    setToken(null)
    setRole(null)
  }

  return (
    <AuthContext.Provider value={{ token, role, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)