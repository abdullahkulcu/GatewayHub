import type { FormEvent, ReactNode } from 'react'

interface AuthCardProps {
  title: string
  error: string | null
  submitLabel: string
  submittingLabel: string
  submitting: boolean
  onSubmit: (event: FormEvent) => void
  children: ReactNode
}

export function AuthCard({
  title,
  error,
  submitLabel,
  submittingLabel,
  submitting,
  onSubmit,
  children,
}: AuthCardProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-neutral-800 bg-neutral-900 p-6"
      >
        <h1 className="text-lg font-semibold text-neutral-100">{title}</h1>
        {error && (
          <p className="rounded border border-red-900 bg-red-950 px-3 py-2 text-sm text-red-400">
            {error}
          </p>
        )}
        {children}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:opacity-50"
        >
          {submitting ? submittingLabel : submitLabel}
        </button>
      </form>
    </div>
  )
}

interface TextFieldProps {
  id: string
  label: string
  type?: string
  value: string
  onChange: (value: string) => void
  autoFocus?: boolean
}

export function TextField({ id, label, type = 'text', value, onChange, autoFocus }: TextFieldProps) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="text-sm text-neutral-400">
        {label}
      </label>
      <input
        id={id}
        type={type}
        required
        autoFocus={autoFocus}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-neutral-100 outline-none focus:border-indigo-500"
      />
    </div>
  )
}
