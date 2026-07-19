import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { TaskFilters } from '../components/TaskFilters'
import { TaskTable } from '../components/TaskTable'
import { TaskDetailPanel } from '../components/TaskDetailPanel'
import { useTasks, useUsersDirectory } from '../shared/queries'
import { useSelectedTask } from '../shared/useSelectedTask'
import { isTypingTarget } from '../shared/keyboard'

const DEFAULT_SORT = 'title'

export function TasksListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { selectedTaskId, select, clear } = useSelectedTask()
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null)

  const assignee = searchParams.get('assignee') ?? undefined
  const status = searchParams.get('status') ?? undefined
  const tag = searchParams.get('tag') ?? undefined
  const listId = searchParams.get('list_id') ?? undefined
  const hasParent = searchParams.has('has_parent')
    ? searchParams.get('has_parent') === 'true'
    : undefined
  const sort = searchParams.get('sort') ?? DEFAULT_SORT

  const tasksQuery = useTasks({ assignee, status, tag, listId, hasParent, sort })
  const tasks = useMemo(() => tasksQuery.data ?? [], [tasksQuery.data])
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

  // j/k row navigation + Enter to open the detail panel (FR-UI-3). Status/
  // assignee quick-change shortcuts are NOT implemented here: those write
  // back to the provider, which doesn't exist until Phase 1 — same
  // reasoning as skipping board drag-and-drop in T22.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (isTypingTarget(event.target) || tasks.length === 0) return
      if (event.key === 'j') {
        event.preventDefault()
        setFocusedIndex((i) => (i === null ? 0 : Math.min(i + 1, tasks.length - 1)))
      } else if (event.key === 'k') {
        event.preventDefault()
        setFocusedIndex((i) => (i === null ? 0 : Math.max(i - 1, 0)))
      } else if (event.key === 'Enter' && focusedIndex !== null && tasks[focusedIndex]) {
        select(tasks[focusedIndex].id)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [tasks, focusedIndex, select])

  useEffect(() => {
    setFocusedIndex(null)
  }, [assignee, status, tag, listId, hasParent, sort])

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
          tasks={tasks}
          usersById={usersById}
          sort={sort}
          onSort={handleSort}
          onSelect={select}
          focusedIndex={focusedIndex}
        />
      )}
      {selectedTaskId && (
        <TaskDetailPanel taskId={selectedTaskId} usersById={usersById} onClose={clear} />
      )}
    </AppShell>
  )
}
