import type { ReactNode } from 'react'

export function SettingsCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
      <h2 className="mb-3 text-sm font-semibold text-neutral-200">{title}</h2>
      {children}
    </section>
  )
}

export const inputClasses =
  'rounded border border-neutral-700 bg-neutral-950 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-indigo-500'

export const buttonClasses =
  'rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50'

export const secondaryButtonClasses =
  'rounded border border-neutral-700 px-3 py-1.5 text-sm text-neutral-300 hover:border-neutral-600 disabled:opacity-50'
