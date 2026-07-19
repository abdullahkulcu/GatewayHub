import { useState, type ReactNode } from 'react'
import { getToken, setToken as persistToken, clearToken } from './auth'
import { AuthContext } from './authContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => getToken())

  function login(newToken: string): void {
    persistToken(newToken)
    setTokenState(newToken)
  }

  function logout(): void {
    clearToken()
    setTokenState(null)
  }

  return <AuthContext.Provider value={{ token, login, logout }}>{children}</AuthContext.Provider>
}
