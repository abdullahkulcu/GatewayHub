import type { TaskSummary } from '../shared/types'

interface TaskCardProps {
  task: TaskSummary
  parentTitle?: string
  usersById: Map<string, string>
  onSelect: (taskId: string) => void
}

export function TaskCard({ task, parentTitle, usersById, onSelect }: TaskCardProps) {
  const assigneeLabels = (task.assignees ?? []).map((id) => usersById.get(id) ?? id)

  return (
    <div
      onClick={() => onSelect(task.id)}
      className="cursor-pointer rounded border border-neutral-800 bg-neutral-900 p-3 text-sm hover:border-neutral-700"
    >
      {parentTitle && (
        <div className="mb-1 truncate text-xs text-neutral-500" title={parentTitle}>
          ↳ {parentTitle}
        </div>
      )}
      <div className="font-medium text-neutral-100">{task.title}</div>
      <div className="mt-1 flex flex-wrap gap-x-2 text-xs text-neutral-500">
        {task.provider_list_name && <span>{task.provider_list_name}</span>}
        {task.priority && <span>{task.priority}</span>}
      </div>
      {assigneeLabels.length > 0 && (
        <div className="mt-1 truncate text-xs text-neutral-500">{assigneeLabels.join(', ')}</div>
      )}
    </div>
  )
}
