import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './shared/AuthContext.tsx'
import { ApiError } from './shared/api.ts'
import { clearToken } from './shared/auth.ts'

function handleQueryError(error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    clearToken()
    if (window.location.pathname !== '/login') window.location.assign('/login')
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: handleQueryError }),
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
