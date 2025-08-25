import React, { createContext, useContext, useState } from 'react'
import { ConnectRequest, connect, setCredentials } from '@api/api'

interface AuthContextType {
  connected: boolean
  login: (payload: ConnectRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  connected: false,
  login: async () => {},
  logout: () => {},
})

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connected, setConnected] = useState<boolean>(!!localStorage.getItem('creds'))

  const login = async (payload: ConnectRequest) => {
    // Validate connection (password or access_token)
    await connect(payload)
    // Persist credentials for stateless requests
    setCredentials(payload)
    setConnected(true)
  }

  const logout = () => {
    setCredentials(null)
    setConnected(false)
  }

  return (
    <AuthContext.Provider value={{ connected, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)