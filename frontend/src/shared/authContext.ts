import { createContext } from 'react'

export interface AuthState {
  token: string | null
  login: (token: string) => void
  logout: () => void
}

export const AuthContext = createContext<AuthState | null>(null)
