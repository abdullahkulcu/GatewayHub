import { useSyncStatus } from '../../shared/queries'
import { SettingsCard } from './SettingsCard'

function formatDateTime(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : '—'
}

export function SyncStatusCard() {
  const { data } = useSyncStatus()

  return (
    <SettingsCard title="Sync status">
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <dt className="text-neutral-500">Last synced</dt>
        <dd className="text-neutral-200">{formatDateTime(data?.last_synced_at)}</dd>
        <dt className="text-neutral-500">Next poll</dt>
        <dd className="text-neutral-200">{formatDateTime(data?.next_poll_at)}</dd>
      </dl>
      {data?.last_sync_error && (
        <p className="mt-2 rounded border border-red-900 bg-red-950 px-3 py-2 text-sm text-red-400">
          {data.last_sync_error}
        </p>
      )}
    </SettingsCard>
  )
}
