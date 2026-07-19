import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../shared/api'
import { useSettings } from '../../shared/queries'
import { SettingsCard, buttonClasses, inputClasses } from './SettingsCard'

export function PollIntervalCard() {
  const queryClient = useQueryClient()
  const settingsQuery = useSettings()
  const [seconds, setSeconds] = useState(60)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (settingsQuery.data) setSeconds(settingsQuery.data.poll_interval_seconds)
  }, [settingsQuery.data])

  async function handleSave() {
    setError(null)
    setSaving(true)
    try {
      await api.put('/api/settings/poll-interval', { poll_interval_seconds: seconds })
      await queryClient.invalidateQueries({ queryKey: ['settings'] })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <SettingsCard title="Poll interval">
      <div className="flex items-end gap-2">
        <label className="flex flex-col gap-1 text-xs text-neutral-400">
          Seconds between syncs
          <input
            type="number"
            min={1}
            value={seconds}
            onChange={(e) => setSeconds(Number(e.target.value))}
            className={`${inputClasses} w-32`}
          />
        </label>
        <button type="button" onClick={handleSave} disabled={saving} className={buttonClasses}>
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </SettingsCard>
  )
}
