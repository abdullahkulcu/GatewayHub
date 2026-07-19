import { AppShell } from '../components/AppShell'
import { ClickUpConnectionCard } from '../components/settings/ClickUpConnectionCard'
import { SyncScopeCard } from '../components/settings/SyncScopeCard'
import { PollIntervalCard } from '../components/settings/PollIntervalCard'
import { SyncStatusCard } from '../components/settings/SyncStatusCard'
import { UserManagementCard } from '../components/settings/UserManagementCard'
import { useMe } from '../shared/queries'

export function SettingsPage() {
  const meQuery = useMe()

  if (meQuery.data && meQuery.data.role !== 'admin') {
    return (
      <AppShell>
        <p className="text-sm text-neutral-400">
          Settings are only available to admins. Ask an admin to make changes here.
        </p>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-lg font-semibold">Settings</h1>
      <div className="grid max-w-3xl gap-4">
        <ClickUpConnectionCard />
        <SyncScopeCard />
        <PollIntervalCard />
        <SyncStatusCard />
        <UserManagementCard />
      </div>
    </AppShell>
  )
}
