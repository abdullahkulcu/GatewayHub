import { useState, type FormEvent } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../shared/api'
import { useUsers } from '../../shared/queries'
import type { UserRole } from '../../shared/types'
import { SettingsCard, buttonClasses, inputClasses, secondaryButtonClasses } from './SettingsCard'

export function UserManagementCard() {
  const queryClient = useQueryClient()
  const usersQuery = useUsers()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>('member')
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [resettingUserId, setResettingUserId] = useState<string | null>(null)
  const [resetPasswordValue, setResetPasswordValue] = useState('')

  async function invalidate() {
    await queryClient.invalidateQueries({ queryKey: ['users'] })
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setCreating(true)
    try {
      await api.post('/api/users', { email, password, role })
      setEmail('')
      setPassword('')
      setRole('member')
      await invalidate()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(userId: string) {
    setError(null)
    try {
      await api.delete(`/api/users/${userId}`)
      await invalidate()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    }
  }

  async function handleResetPassword(userId: string) {
    setError(null)
    try {
      await api.post(`/api/users/${userId}/reset-password`, {
        new_password: resetPasswordValue,
      })
      setResettingUserId(null)
      setResetPasswordValue('')
      await invalidate()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    }
  }

  return (
    <SettingsCard title="Users">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-neutral-800 text-neutral-400">
            <th className="px-2 py-1.5 font-medium">Email</th>
            <th className="px-2 py-1.5 font-medium">Role</th>
            <th className="px-2 py-1.5 font-medium">Status</th>
            <th className="px-2 py-1.5 font-medium" />
          </tr>
        </thead>
        <tbody>
          {(usersQuery.data ?? []).map((user) => (
            <tr key={user.id} className="border-b border-neutral-900">
              <td className="px-2 py-1.5 text-neutral-200">{user.email}</td>
              <td className="px-2 py-1.5 text-neutral-400">{user.role}</td>
              <td className="px-2 py-1.5 text-neutral-400">
                {user.must_change_password ? 'Pending password change' : 'Active'}
              </td>
              <td className="px-2 py-1.5">
                {resettingUserId === user.id ? (
                  <div className="flex items-center gap-1">
                    <input
                      type="password"
                      value={resetPasswordValue}
                      onChange={(e) => setResetPasswordValue(e.target.value)}
                      placeholder="New password"
                      className={inputClasses}
                    />
                    <button
                      type="button"
                      onClick={() => handleResetPassword(user.id)}
                      className={buttonClasses}
                    >
                      Confirm
                    </button>
                    <button
                      type="button"
                      onClick={() => setResettingUserId(null)}
                      className={secondaryButtonClasses}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setResettingUserId(user.id)
                        setResetPasswordValue('')
                      }}
                      className={secondaryButtonClasses}
                    >
                      Reset password
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(user.id)}
                      className={secondaryButtonClasses}
                    >
                      Delete
                    </button>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <form onSubmit={handleCreate} className="mt-4 flex items-end gap-2">
        <label className="flex flex-col gap-1 text-xs text-neutral-400">
          Email
          <input
            type="text"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClasses}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-neutral-400">
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClasses}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-neutral-400">
          Role
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            className={inputClasses}
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <button type="submit" disabled={creating} className={buttonClasses}>
          {creating ? 'Adding…' : 'Add user'}
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </SettingsCard>
  )
}
