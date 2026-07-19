import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../shared/api'
import { useClickUpLists, useClickUpWorkspaces, useSettings } from '../../shared/queries'
import { SettingsCard, buttonClasses, inputClasses } from './SettingsCard'

export function SyncScopeCard() {
  const queryClient = useQueryClient()
  const settingsQuery = useSettings()
  const tokenConfigured = settingsQuery.data?.clickup_token_configured ?? false
  const workspacesQuery = useClickUpWorkspaces(tokenConfigured)

  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined)
  const [selectedListIds, setSelectedListIds] = useState<Set<string>>(new Set())
  const [initialized, setInitialized] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const listsQuery = useClickUpLists(workspaceId)

  useEffect(() => {
    if (!initialized && settingsQuery.data?.sync_scope) {
      setWorkspaceId(settingsQuery.data.sync_scope.workspace_id)
      setSelectedListIds(new Set(settingsQuery.data.sync_scope.list_ids))
      setInitialized(true)
    }
  }, [initialized, settingsQuery.data])

  function toggleList(listId: string) {
    setSelectedListIds((prev) => {
      const next = new Set(prev)
      if (next.has(listId)) next.delete(listId)
      else next.add(listId)
      return next
    })
  }

  async function handleSave() {
    if (!workspaceId) return
    setError(null)
    setSaving(true)
    try {
      await api.put('/api/settings/sync-scope', {
        workspace_id: workspaceId,
        list_ids: Array.from(selectedListIds),
      })
      await queryClient.invalidateQueries({ queryKey: ['settings'] })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    } finally {
      setSaving(false)
    }
  }

  if (!tokenConfigured) {
    return (
      <SettingsCard title="Sync scope">
        <p className="text-sm text-neutral-500">Configure a ClickUp token first.</p>
      </SettingsCard>
    )
  }

  return (
    <SettingsCard title="Sync scope">
      <label className="flex flex-col gap-1 text-xs text-neutral-400">
        Workspace
        <select
          className={inputClasses}
          value={workspaceId ?? ''}
          onChange={(e) => {
            setWorkspaceId(e.target.value || undefined)
            setSelectedListIds(new Set())
          }}
        >
          <option value="">Select a workspace…</option>
          {(workspacesQuery.data ?? []).map((workspace) => (
            <option key={workspace.id} value={workspace.id}>
              {workspace.name}
            </option>
          ))}
        </select>
      </label>

      {workspaceId && (
        <div className="mt-3">
          <p className="mb-1 text-xs text-neutral-400">Lists to sync</p>
          {listsQuery.isLoading && <p className="text-sm text-neutral-500">Loading lists…</p>}
          <ul className="max-h-48 space-y-1 overflow-y-auto">
            {(listsQuery.data ?? []).map((list) => (
              <li key={list.id}>
                <label className="flex items-center gap-2 text-sm text-neutral-300">
                  <input
                    type="checkbox"
                    checked={selectedListIds.has(list.id)}
                    onChange={() => toggleList(list.id)}
                  />
                  {list.name}
                  {list.folder_name && (
                    <span className="text-xs text-neutral-600">
                      {list.space_name} / {list.folder_name}
                    </span>
                  )}
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        type="button"
        onClick={handleSave}
        disabled={saving || !workspaceId}
        className={`${buttonClasses} mt-3`}
      >
        {saving ? 'Saving…' : 'Save scope'}
      </button>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </SettingsCard>
  )
}
