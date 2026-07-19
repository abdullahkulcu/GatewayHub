import type { TaskSummary } from '../shared/types'

interface TaskTableProps {
  tasks: TaskSummary[]
  usersById: Map<string, string>
  sort: string
  onSort: (column: string) => void
  onSelect: (taskId: string) => void
}

const COLUMNS: { key: string; label: string; sortable: boolean }[] = [
  { key: 'title', label: 'Title', sortable: true },
  { key: 'list', label: 'List', sortable: false },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'assignees', label: 'Assignees', sortable: false },
  { key: 'priority', label: 'Priority', sortable: true },
  { key: 'due_date', label: 'Due', sortable: true },
]

function sortIndicator(sort: string, column: string): string {
  if (sort === column) return ' ▲'
  if (sort === `-${column}`) return ' ▼'
  return ''
}

const STATUS_CATEGORY_COLOR: Record<string, string> = {
  todo: 'bg-neutral-700 text-neutral-200',
  in_progress: 'bg-indigo-900 text-indigo-200',
  done: 'bg-emerald-900 text-emerald-200',
  cancelled: 'bg-red-950 text-red-300',
}

export function TaskTable({ tasks, usersById, sort, onSort, onSelect }: TaskTableProps) {
  if (tasks.length === 0) {
    return <p className="text-sm text-neutral-500">No tasks match the current filters.</p>
  }

  return (
    <table className="w-full border-collapse text-left text-sm">
      <thead>
        <tr className="border-b border-neutral-800 text-neutral-400">
          {COLUMNS.map((col) => (
            <th key={col.key} className="px-3 py-2 font-medium">
              {col.sortable ? (
                <button
                  type="button"
                  onClick={() => onSort(col.key)}
                  className="hover:text-neutral-100"
                >
                  {col.label}
                  {sortIndicator(sort, col.key)}
                </button>
              ) : (
                col.label
              )}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {tasks.map((task) => (
          <tr
            key={task.id}
            onClick={() => onSelect(task.id)}
            className="cursor-pointer border-b border-neutral-900 hover:bg-neutral-900/50"
          >
            <td className="px-3 py-2">
              {task.parent_id && <span className="mr-1 text-neutral-500">↳</span>}
              {task.title}
            </td>
            <td className="px-3 py-2 text-neutral-400">
              {task.provider_list_name ?? task.provider_list_id ?? '—'}
            </td>
            <td className="px-3 py-2">
              <span
                className={`rounded px-2 py-0.5 text-xs ${
                  task.status_category
                    ? STATUS_CATEGORY_COLOR[task.status_category]
                    : 'bg-neutral-800 text-neutral-300'
                }`}
              >
                {task.status}
              </span>
            </td>
            <td className="px-3 py-2 text-neutral-400">
              {(task.assignees ?? []).map((id) => usersById.get(id) ?? id).join(', ') || '—'}
            </td>
            <td className="px-3 py-2 text-neutral-400">{task.priority ?? '—'}</td>
            <td className="px-3 py-2 text-neutral-400">
              {task.due_date ? new Date(task.due_date).toLocaleDateString() : '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
