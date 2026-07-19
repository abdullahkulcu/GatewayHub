import type { TaskSummary } from '../shared/types'
import { TaskCard } from './TaskCard'

interface BoardColumnProps {
  status: string
  tasks: TaskSummary[]
  taskTitleById: Map<string, string>
  usersById: Map<string, string>
  onSelect: (taskId: string) => void
}

export function BoardColumn({
  status,
  tasks,
  taskTitleById,
  usersById,
  onSelect,
}: BoardColumnProps) {
  return (
    <div className="flex w-72 shrink-0 flex-col gap-2">
      <div className="flex items-center justify-between px-1 text-xs font-medium tracking-wide text-neutral-400 uppercase">
        <span>{status}</span>
        <span className="text-neutral-600">{tasks.length}</span>
      </div>
      <div className="flex flex-col gap-2">
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            parentTitle={task.parent_id ? taskTitleById.get(task.parent_id) : undefined}
            usersById={usersById}
            onSelect={onSelect}
          />
        ))}
        {tasks.length === 0 && <p className="px-1 text-xs text-neutral-600">No tasks</p>}
      </div>
    </div>
  )
}
