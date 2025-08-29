// src/components/auth/ProtectedRoute.tsx
// --- agent_meta ---
// role: protected-route
// owner: @frontend
// contract: защищенный роут для authenticated пользователей
// last_reviewed: 2025-08-28
// interfaces:
//   - ProtectedRoute({ children }) -> JSX.Element
//   - автоматическая проверка авторизации через /me API
//   - интеграция с Layout компонентом
// --- /agent_meta ---

import type { ReactNode } from 'react'
import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { Layout } from '../layout/Layout'
import { apiClient } from '../../lib/api'

interface User {
  id: string
  email: string
  org_id: string
  role: string
}

interface ProtectedRouteProps {
  children: ReactNode
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await apiClient.getCurrentUser()
        setUser(userData)
        setError(false)
      } catch (err) {
        console.error('Auth check failed:', err)
        setError(true)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Проверка авторизации...</p>
        </div>
      </div>
    )
  }

  if (error || !user) {
    return <Navigate to="/" replace />
  }

  return (
    <Layout user={user}>
      {children}
    </Layout>
  )
}