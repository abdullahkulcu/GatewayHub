import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../shared/api'
import { useAuth } from '../shared/useAuth'
import { AuthCard, TextField } from '../components/AuthCard'

interface LoginResponse {
  access_token: string
  token_type: string
  must_change_password: boolean
}

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const result = await api.post<LoginResponse>('/api/auth/login', { email, password })
      login(result.access_token)
      navigate(result.must_change_password ? '/change-password' : '/', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthCard
      title="GatewayHub"
      error={error}
      submitLabel="Sign in"
      submittingLabel="Signing in…"
      submitting={submitting}
      onSubmit={handleSubmit}
    >
      <TextField id="email" label="Email" type="email" value={email} onChange={setEmail} autoFocus />
      <TextField id="password" label="Password" type="password" value={password} onChange={setPassword} />
    </AuthCard>
  )
}
