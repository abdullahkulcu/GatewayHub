import { useState, type FormEvent } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../shared/api'
import { useSettings } from '../../shared/queries'
import { SettingsCard, buttonClasses, inputClasses, secondaryButtonClasses } from './SettingsCard'

export function ClickUpConnectionCard() {
  const queryClient = useQueryClient()
  const settingsQuery = useSettings()
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [removing, setRemoving] = useState(false)

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await api.put('/api/settings/clickup-token', { token })
      setToken('')
      await queryClient.invalidateQueries({ queryKey: ['settings'] })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    } finally {
      setSaving(false)
    }
  }

  async function handleRemove() {
    setRemoving(true)
    try {
      await api.delete('/api/settings/clickup-token')
      await queryClient.invalidateQueries({ queryKey: ['settings'] })
    } finally {
      setRemoving(false)
    }
  }

  const settings = settingsQuery.data

  return (
    <SettingsCard title="ClickUp connection">
      {settings?.clickup_token_configured ? (
        <div className="flex items-center justify-between">
          <p className="text-sm text-neutral-400">
            Connected — token{' '}
            <code className="text-neutral-200">{settings.clickup_token_masked}</code>
          </p>
          <button
            type="button"
            onClick={handleRemove}
            disabled={removing}
            className={secondaryButtonClasses}
          >
            {removing ? 'Removing…' : 'Remove'}
          </button>
        </div>
      ) : (
        <p className="mb-2 text-sm text-neutral-500">
          No ClickUp token configured yet. See docs/INTEGRATIONS.md for how to get one.
        </p>
      )}

      <form onSubmit={handleSave} className="mt-3 flex items-end gap-2">
        <label className="flex flex-1 flex-col gap-1 text-xs text-neutral-400">
          {settings?.clickup_token_configured ? 'Replace token' : 'Personal API token'}
          <input
            type="password"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="pk_..."
            className={inputClasses}
          />
        </label>
        <button type="submit" disabled={saving} className={buttonClasses}>
          {saving ? 'Verifying…' : 'Save'}
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </SettingsCard>
  )
}
