import { useState } from 'react'
import { AppShell } from '../components/AppShell'
import { BoardColumn } from '../components/BoardColumn'
import { TaskDetailPanel } from '../components/TaskDetailPanel'
import { useTasks, useUsersDirectory } from '../shared/queries'
import { useSelectedTask } from '../shared/useSelectedTask'
import type { TaskSummary } from '../shared/types'

const CATEGORY_ORDER: Record<string, number> = {
  todo: 0,
  in_progress: 1,
  done: 2,
  cancelled: 3,
}

function computeColumns(tasks: TaskSummary[]): string[] {
  const categoryByStatus = new Map<string, string | null>()
  for (const task of tasks) {
    if (!categoryByStatus.has(task.status)) categoryByStatus.set(task.status, task.status_category)
  }
  return Array.from(categoryByStatus.entries())
    .sort(([statusA, catA], [statusB, catB]) => {
      const rankA = catA ? (CATEGORY_ORDER[catA] ?? 99) : 99
      const rankB = catB ? (CATEGORY_ORDER[catB] ?? 99) : 99
      if (rankA !== rankB) return rankA - rankB
      return statusA.localeCompare(statusB)
    })
    .map(([status]) => status)
}

export function BoardPage() {
  const [showSubtasks, setShowSubtasks] = useState(true)
  const tasksQuery = useTasks({ sort: 'title' })
  const usersQuery = useUsersDirectory()
  const { selectedTaskId, select, clear } = useSelectedTask()

  const allTasks = tasksQuery.data ?? []
  const visibleTasks = showSubtasks ? allTasks : allTasks.filter((t) => t.parent_id === null)
  const columns = computeColumns(visibleTasks)
  const taskTitleById = new Map(allTasks.map((t) => [t.id, t.title]))
  const usersById = new Map((usersQuery.data ?? []).map((u) => [u.id, u.email]))

  return (
    <AppShell>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Board</h1>
        <label className="flex items-center gap-2 text-sm text-neutral-400">
          <input
            type="checkbox"
            checked={showSubtasks}
            onChange={(e) => setShowSubtasks(e.target.checked)}
          />
          Show subtasks as cards
        </label>
      </div>
      {tasksQuery.isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
      {tasksQuery.isError && (
        <p className="text-sm text-red-400">Couldn't load tasks. Try again shortly.</p>
      )}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((status) => (
          <BoardColumn
            key={status}
            status={status}
            tasks={visibleTasks.filter((t) => t.status === status)}
            taskTitleById={taskTitleById}
            usersById={usersById}
            onSelect={select}
          />
        ))}
      </div>
      {selectedTaskId && (
        <TaskDetailPanel taskId={selectedTaskId} usersById={usersById} onClose={clear} />
      )}
    </AppShell>
  )
}
