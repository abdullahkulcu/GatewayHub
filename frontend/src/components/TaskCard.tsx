import type { TaskSummary } from '../shared/types'

interface TaskCardProps {
  task: TaskSummary
  parentTitle?: string
  usersById: Map<string, string>
}

export function TaskCard({ task, parentTitle, usersById }: TaskCardProps) {
  const assigneeLabels = (task.assignees ?? []).map((id) => usersById.get(id) ?? id)

  return (
    <div className="rounded border border-neutral-800 bg-neutral-900 p-3 text-sm">
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
