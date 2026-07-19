import { useSearchParams } from 'react-router-dom'

export function useSelectedTask() {
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedTaskId = searchParams.get('task') ?? undefined

  function select(taskId: string): void {
    const next = new URLSearchParams(searchParams)
    next.set('task', taskId)
    setSearchParams(next)
  }

  function clear(): void {
    const next = new URLSearchParams(searchParams)
    next.delete('task')
    setSearchParams(next)
  }

  return { selectedTaskId, select, clear }
}
