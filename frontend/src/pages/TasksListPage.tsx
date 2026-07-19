import { useSearchParams } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { TaskFilters } from '../components/TaskFilters'
import { TaskTable } from '../components/TaskTable'
import { useTasks, useUsersDirectory } from '../shared/queries'

const DEFAULT_SORT = 'title'

export function TasksListPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const assignee = searchParams.get('assignee') ?? undefined
  const status = searchParams.get('status') ?? undefined
  const tag = searchParams.get('tag') ?? undefined
  const listId = searchParams.get('list_id') ?? undefined
  const hasParent = searchParams.has('has_parent')
    ? searchParams.get('has_parent') === 'true'
    : undefined
  const sort = searchParams.get('sort') ?? DEFAULT_SORT

  const tasksQuery = useTasks({ assignee, status, tag, listId, hasParent, sort })
  const usersQuery = useUsersDirectory()
  const usersById = new Map((usersQuery.data ?? []).map((u) => [u.id, u.email]))

  function patchParams(patch: Record<string, string | boolean | undefined>) {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(patch)) {
      const paramKey = key === 'listId' ? 'list_id' : key === 'hasParent' ? 'has_parent' : key
      if (value === undefined) next.delete(paramKey)
      else next.set(paramKey, String(value))
    }
    setSearchParams(next)
  }

  function handleSort(column: string) {
    patchParams({ sort: sort === column ? `-${column}` : column })
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-lg font-semibold">Tasks</h1>
      <TaskFilters
        assignee={assignee}
        status={status}
        tag={tag}
        listId={listId}
        hasParent={hasParent}
        onChange={patchParams}
      />
      {tasksQuery.isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
      {tasksQuery.isError && (
        <p className="text-sm text-red-400">Couldn't load tasks. Try again shortly.</p>
      )}
      {tasksQuery.data && (
        <TaskTable
          tasks={tasksQuery.data}
          usersById={usersById}
          sort={sort}
          onSort={handleSort}
        />
      )}
    </AppShell>
  )
}
