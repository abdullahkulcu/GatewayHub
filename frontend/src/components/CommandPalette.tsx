import { useEffect, useRef, useState } from 'react'
import { useTasks } from '../shared/queries'
import { useSelectedTask } from '../shared/useSelectedTask'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const tasksQuery = useTasks({})
  const { select } = useSelectedTask()

  const results = (tasksQuery.data ?? [])
    .filter((task) => task.title.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 8)

  useEffect(() => {
    function handleGlobalKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setOpen((prev) => !prev)
      } else if (event.key === 'Escape' && open) {
        setOpen(false)
      }
    }
    document.addEventListener('keydown', handleGlobalKeyDown)
    return () => document.removeEventListener('keydown', handleGlobalKeyDown)
  }, [open])

  useEffect(() => {
    if (open) {
      setQuery('')
      setActiveIndex(0)
      inputRef.current?.focus()
    }
  }, [open])

  useEffect(() => {
    setActiveIndex(0)
  }, [query])

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, results.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (event.key === 'Enter' && results[activeIndex]) {
      select(results[activeIndex].id)
      setOpen(false)
    }
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-30 flex items-start justify-center bg-black/50 pt-24"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-lg rounded-lg border border-neutral-800 bg-neutral-900 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Jump to a task…"
          className="w-full border-b border-neutral-800 bg-transparent px-4 py-3 text-neutral-100 outline-none"
        />
        <ul className="max-h-80 overflow-y-auto py-1">
          {results.length === 0 && (
            <li className="px-4 py-2 text-sm text-neutral-500">No matching tasks.</li>
          )}
          {results.map((task, index) => (
            <li
              key={task.id}
              onClick={() => {
                select(task.id)
                setOpen(false)
              }}
              className={`cursor-pointer px-4 py-2 text-sm ${
                index === activeIndex ? 'bg-indigo-600 text-white' : 'text-neutral-200'
              }`}
            >
              {task.title}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
