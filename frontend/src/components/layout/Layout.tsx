// src/components/layout/Layout.tsx
// --- agent_meta ---
// role: layout-component
// owner: @frontend
// contract: основной layout с навигацией и header для authenticated страниц
// last_reviewed: 2025-08-28
// interfaces:
//   - Layout({ children, user }) -> JSX.Element
//   - Navigation компонент с роутингом
//   - UserMenu с logout и профилем
// --- /agent_meta ---

import { ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Home, User, LogOut } from 'lucide-react'
import { apiClient } from '../../lib/api'

interface User {
  id: string
  email: string
}

interface LayoutProps {
  children: ReactNode
  user: User
}

export const Layout = ({ children, user }: LayoutProps) => {
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await apiClient.logout()
      navigate('/')
    } catch (error) {
      console.error('Logout error:', error)
      // Even if logout fails, redirect to auth page
      navigate('/')
    }
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Navigation */}
            <div className="flex items-center space-x-8">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-gray-900">
                  AI Career Tools
                </h1>
              </div>
              
              <nav className="hidden md:flex space-x-8">
                <Link
                  to="/dashboard"
                  className={`inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 transition-colors ${
                    isActive('/dashboard')
                      ? 'border-indigo-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Home className="w-4 h-4 mr-2" />
                  Главная
                </Link>
                <Link
                  to="/profile"
                  className={`inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 transition-colors ${
                    isActive('/profile')
                      ? 'border-indigo-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <User className="w-4 h-4 mr-2" />
                  Профиль
                </Link>
              </nav>
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-indigo-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">
                    {user.email}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-gray-400 hover:text-gray-500 rounded-md hover:bg-gray-100 transition-colors"
                  title="Выйти"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {children}
        </div>
      </main>
    </div>
  )
}