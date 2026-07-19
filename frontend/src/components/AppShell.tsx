import type { ReactNode } from 'react'
import { useAuth } from '../shared/useAuth'

export function AppShell({ children }: { children: ReactNode }) {
  const { logout } = useAuth()

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <header className="flex items-center justify-between border-b border-neutral-800 px-6 py-3">
        <span className="font-semibold">GatewayHub</span>
        <button
          type="button"
          onClick={logout}
          className="text-sm text-neutral-400 hover:text-neutral-100"
        >
          Sign out
        </button>
      </header>
      <main className="p-6">{children}</main>
    </div>
  )
}
