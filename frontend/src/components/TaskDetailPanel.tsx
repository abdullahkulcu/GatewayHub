import { useEffect } from 'react'
import Markdown from 'react-markdown'
import { useTask } from '../shared/queries'

interface TaskDetailPanelProps {
  taskId: string
  usersById: Map<string, string>
  onClose: () => void
}

function formatDateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString() : '—'
}

export function TaskDetailPanel({ taskId, usersById, onClose }: TaskDetailPanelProps) {
  const { data: task, isLoading, isError } = useTask(taskId)

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-20 flex justify-end bg-black/50" onClick={onClose}>
      <div
        className="h-full w-full max-w-lg overflow-y-auto border-l border-neutral-800 bg-neutral-950 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold text-neutral-100">{task?.title ?? 'Loading…'}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="shrink-0 text-neutral-500 hover:text-neutral-200"
          >
            ✕
          </button>
        </div>

        {isLoading && <p className="text-sm text-neutral-500">Loading…</p>}
        {isError && <p className="text-sm text-red-400">Couldn't load this task.</p>}

        {task && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-400">
              <span className="rounded bg-neutral-800 px-2 py-0.5">{task.status}</span>
              {task.provider_list_name && <span>{task.provider_list_name}</span>}
              {task.priority && <span>{task.priority}</span>}
              {task.due_date && <span>Due {new Date(task.due_date).toLocaleDateString()}</span>}
            </div>

            {(task.assignees ?? []).length > 0 && (
              <p className="text-sm text-neutral-400">
                Assignees: {(task.assignees ?? []).map((id) => usersById.get(id) ?? id).join(', ')}
              </p>
            )}

            <section>
              <h3 className="mb-2 text-sm font-medium text-neutral-300">Description</h3>
              {task.description ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <Markdown>{task.description}</Markdown>
                </div>
              ) : (
                <p className="text-sm text-neutral-600">No description.</p>
              )}
            </section>

            <section>
              <h3 className="mb-2 text-sm font-medium text-neutral-300">
                Subtasks ({task.subtasks.length})
              </h3>
              {task.subtasks.length === 0 ? (
                <p className="text-sm text-neutral-600">No subtasks.</p>
              ) : (
                <ul className="space-y-1">
                  {task.subtasks.map((subtask) => (
                    <li key={subtask.id} className="text-sm text-neutral-300">
                      <span className="mr-2 rounded bg-neutral-800 px-1.5 py-0.5 text-xs">
                        {subtask.status}
                      </span>
                      {subtask.title}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <h3 className="mb-2 text-sm font-medium text-neutral-300">
                Comments ({task.comments.length})
              </h3>
              {task.comments.length === 0 ? (
                <p className="text-sm text-neutral-600">No comments.</p>
              ) : (
                <ul className="space-y-3">
                  {task.comments.map((comment) => (
                    <li key={comment.id} className="rounded border border-neutral-800 p-2 text-sm">
                      <div className="mb-1 flex justify-between text-xs text-neutral-500">
                        <span>{comment.author}</span>
                        <span>{formatDateTime(comment.created_at)}</span>
                      </div>
                      <p className="text-neutral-200">{comment.body}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <h3 className="mb-2 text-sm font-medium text-neutral-300">Activity</h3>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-neutral-500">
                <dt>Sync state</dt>
                <dd className="text-neutral-300">{task.write_state}</dd>
                <dt>Last synced</dt>
                <dd className="text-neutral-300">{formatDateTime(task.last_synced_at)}</dd>
                <dt>Provider updated</dt>
                <dd className="text-neutral-300">{formatDateTime(task.provider_updated_at)}</dd>
                <dt>Sync version</dt>
                <dd className="text-neutral-300">{task.sync_version}</dd>
              </dl>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
