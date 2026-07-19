import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../shared/useAuth'
import { useMe } from '../shared/queries'
import { CommandPalette } from './CommandPalette'

function navClasses({ isActive }: { isActive: boolean }): string {
  return `text-sm ${isActive ? 'text-neutral-100' : 'text-neutral-500 hover:text-neutral-300'}`
}

export function AppShell({ children }: { children: ReactNode }) {
  const { logout } = useAuth()
  const meQuery = useMe()
  const isAdmin = meQuery.data?.role === 'admin'

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <header className="flex items-center justify-between border-b border-neutral-800 px-6 py-3">
        <div className="flex items-center gap-6">
          <span className="font-semibold">GatewayHub</span>
          <nav className="flex gap-4">
            <NavLink to="/" end className={navClasses}>
              Tasks
            </NavLink>
            <NavLink to="/board" className={navClasses}>
              Board
            </NavLink>
            {isAdmin && (
              <NavLink to="/settings" className={navClasses}>
                Settings
              </NavLink>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-neutral-600">⌘K to search</span>
          <button
            type="button"
            onClick={logout}
            className="text-sm text-neutral-400 hover:text-neutral-100"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="p-6">{children}</main>
      <CommandPalette />
    </div>
  )
}
