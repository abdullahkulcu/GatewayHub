import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../shared/api'
import { AuthCard, TextField } from '../components/AuthCard'

export function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await api.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthCard
      title="Choose a new password"
      error={error}
      submitLabel="Update password"
      submittingLabel="Updating…"
      submitting={submitting}
      onSubmit={handleSubmit}
    >
      <p className="text-sm text-neutral-400">
        This is your first sign-in — set a new password before continuing.
      </p>
      <TextField
        id="current-password"
        label="Current password"
        type="password"
        value={currentPassword}
        onChange={setCurrentPassword}
        autoFocus
      />
      <TextField
        id="new-password"
        label="New password"
        type="password"
        value={newPassword}
        onChange={setNewPassword}
      />
    </AuthCard>
  )
}
