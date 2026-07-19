import { useState, type KeyboardEvent } from 'react'
import { useListOptions, useUsersDirectory } from '../shared/queries'

interface TaskFiltersProps {
  assignee?: string
  status?: string
  tag?: string
  listId?: string
  hasParent?: boolean
  onChange: (patch: {
    assignee?: string
    status?: string
    tag?: string
    listId?: string
    hasParent?: boolean
  }) => void
}

function selectClasses() {
  return 'rounded border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100'
}

export function TaskFilters({ assignee, status, tag, listId, hasParent, onChange }: TaskFiltersProps) {
  const usersQuery = useUsersDirectory()
  const listOptionsQuery = useListOptions()
  const [statusDraft, setStatusDraft] = useState(status ?? '')
  const [tagDraft, setTagDraft] = useState(tag ?? '')

  function applyTextFilter(key: 'status' | 'tag', value: string) {
    onChange({ [key]: value || undefined })
  }

  function handleKeyDown(key: 'status' | 'tag', value: string) {
    return (event: KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter') applyTextFilter(key, value)
    }
  }

  return (
    <div className="mb-4 flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1 text-xs text-neutral-400">
        Assignee
        <select
          className={selectClasses()}
          value={assignee ?? ''}
          onChange={(e) => onChange({ assignee: e.target.value || undefined })}
        >
          <option value="">All</option>
          {(usersQuery.data ?? []).map((u) => (
            <option key={u.id} value={u.id}>
              {u.email}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-xs text-neutral-400">
        Status
        <input
          className={selectClasses()}
          value={statusDraft}
          placeholder="e.g. in progress"
          onChange={(e) => setStatusDraft(e.target.value)}
          onBlur={() => applyTextFilter('status', statusDraft)}
          onKeyDown={handleKeyDown('status', statusDraft)}
        />
      </label>

      <label className="flex flex-col gap-1 text-xs text-neutral-400">
        Tag
        <input
          className={selectClasses()}
          value={tagDraft}
          placeholder="e.g. backend"
          onChange={(e) => setTagDraft(e.target.value)}
          onBlur={() => applyTextFilter('tag', tagDraft)}
          onKeyDown={handleKeyDown('tag', tagDraft)}
        />
      </label>

      <label className="flex flex-col gap-1 text-xs text-neutral-400">
        List
        <select
          className={selectClasses()}
          value={listId ?? ''}
          onChange={(e) => onChange({ listId: e.target.value || undefined })}
        >
          <option value="">All</option>
          {(listOptionsQuery.data ?? []).map((l) => (
            <option key={l.id} value={l.id}>
              {l.name ?? l.id}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-xs text-neutral-400">
        Parent
        <select
          className={selectClasses()}
          value={hasParent === undefined ? '' : String(hasParent)}
          onChange={(e) =>
            onChange({ hasParent: e.target.value === '' ? undefined : e.target.value === 'true' })
          }
        >
          <option value="">All</option>
          <option value="true">Subtasks only</option>
          <option value="false">Top-level only</option>
        </select>
      </label>
    </div>
  )
}
