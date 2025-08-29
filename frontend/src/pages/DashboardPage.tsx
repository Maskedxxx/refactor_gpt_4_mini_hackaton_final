// src/pages/DashboardPage.tsx
// --- agent_meta ---
// role: dashboard-page
// owner: @frontend
// contract: главная страница после авторизации с HH статусом и quick actions
// last_reviewed: 2025-08-28
// interfaces:
//   - DashboardPage() -> JSX.Element
//   - HHStatusCard для статуса подключения
//   - QuickActionsPanel с основными действиями
// --- /agent_meta ---

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Rocket, 
  Settings, 
  FolderOpen, 
  CheckCircle, 
  AlertTriangle,
  ExternalLink
} from 'lucide-react'
import { apiClient } from '../lib/api'
import { AIToolsList } from '../components/ai/AIToolsList'

interface HHStatus {
  is_connected: boolean
  expires_in_seconds?: number
  connected_at?: number
  account_info?: {
    email?: string
    name?: string
  }
}

const DashboardPage = () => {
  const [hhStatus, setHhStatus] = useState<HHStatus | null>(null)
  const [hhLoading, setHhLoading] = useState(true)

  useEffect(() => {
    const fetchHHStatus = async () => {
      try {
        const status = await apiClient.getHHStatus()
        setHhStatus(status)
      } catch (error) {
        console.error('Failed to fetch HH status:', error)
        setHhStatus({ is_connected: false })
      } finally {
        setHhLoading(false)
      }
    }

    fetchHHStatus()
  }, [])

  // Обновляем статус когда пользователь возвращается на вкладку
  useEffect(() => {
    const handleFocus = async () => {
      if (document.visibilityState === 'visible') {
        try {
          const status = await apiClient.getHHStatus()
          setHhStatus(status)
        } catch (error) {
          console.error('Failed to refresh HH status:', error)
        }
      }
    }

    document.addEventListener('visibilitychange', handleFocus)
    window.addEventListener('focus', handleFocus)

    return () => {
      document.removeEventListener('visibilitychange', handleFocus)
      window.removeEventListener('focus', handleFocus)
    }
  }, [])

  const handleConnectHH = async () => {
    try {
      await apiClient.connectToHH()
      // Если код дошел сюда без ошибки, но redirect не произошел
      console.log('Unexpected: connect completed without redirect')
    } catch (error: any) {
      // Проверяем - это ошибка "уже подключен"?
      const is409 = 
        error.status === 409 || 
        error.response?.status === 409 || 
        (error.response?.data?.detail?.error_code === 'HH_ALREADY_CONNECTED')
      
      if (is409) {
        console.log('HH уже подключен, обновляем статус...')
        // Принудительно устанавливаем статус "подключен"
        setHhStatus({ is_connected: true })
        setHhLoading(false)
        
        // Также обновляем с сервера для получения полной информации
        refreshHHStatus().catch(err => console.warn('Не удалось обновить статус с сервера:', err))
      } else {
        console.error('Ошибка подключения к HH.ru:', error.message || 'Неизвестная ошибка')
      }
    }
  }

  const refreshHHStatus = async () => {
    setHhLoading(true)
    try {
      const status = await apiClient.getHHStatus()
      setHhStatus(status)
    } catch (error) {
      console.error('Failed to refresh HH status:', error)
    } finally {
      setHhLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Welcome Hero Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="max-w-3xl">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            👋 Добро пожаловать в AI Career Tools!
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            Создавайте профессиональные материалы для карьеры с помощью искусственного интеллекта. 
            Загрузите резюме, найдите вакансию и получите персонализированные рекомендации.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4">
            <Link
              to="/project/create"
              className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
            >
              <Rocket className="w-5 h-5 mr-2" />
              Создать новый анализ
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content - Left Column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Quick Actions Panel */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              🔧 Быстрые действия
            </h2>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                to="/project/create"
                className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors group"
              >
                <div className="flex-shrink-0">
                  <FolderOpen className="w-8 h-8 text-indigo-600 group-hover:text-indigo-700" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-900">Новый проект</h3>
                  <p className="text-sm text-gray-500">Загрузить резюме и вакансию</p>
                </div>
              </Link>

              <Link
                to="/projects"
                className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors group"
              >
                <div className="flex-shrink-0">
                  <FolderOpen className="w-8 h-8 text-gray-600 group-hover:text-indigo-700" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-900">История проектов</h3>
                  <p className="text-sm text-gray-500">Предыдущие анализы</p>
                </div>
              </Link>
            </div>
          </div>

          {/* AI Tools Preview */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              🤖 Доступные AI инструменты
            </h2>
            
            <AIToolsList showAsButtons={false} />
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* HH.ru Status Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              🔗 HH.ru Статус
            </h2>
            
{hhLoading ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Статус и кнопка обновления */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {hhStatus?.is_connected ? (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        <span className="text-sm font-medium text-green-700">Подключен</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-5 h-5 text-red-500" />
                        <span className="text-sm font-medium text-red-700">Не подключен</span>
                      </>
                    )}
                  </div>
                  <button
                    onClick={refreshHHStatus}
                    className="text-gray-400 hover:text-gray-600 p-1 rounded"
                    title="Обновить статус"
                  >
                    🔄
                  </button>
                </div>

                {/* Информация о подключенном аккаунте */}
                {hhStatus?.is_connected && hhStatus.account_info?.email && (
                  <div>
                    <p className="text-sm text-gray-600">Аккаунт:</p>
                    <p className="text-sm font-medium text-gray-900">
                      {hhStatus.account_info.email}
                    </p>
                  </div>
                )}

                {/* Единая кнопка с цветовой индикацией */}
                <div className="flex flex-col space-y-2">
                  {hhStatus?.is_connected ? (
                    <button
                      className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors cursor-default"
                      disabled
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      ✅ HH.ru подключен
                    </button>
                  ) : (
                    <button
                      onClick={handleConnectHH}
                      className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      ❌ Подключить HH.ru
                    </button>
                  )}
                  
                  {!hhStatus?.is_connected && (
                    <p className="text-xs text-gray-500 text-center">
                      После авторизации на HH.ru статус обновится автоматически
                    </p>
                  )}
                </div>

                {/* Дополнительные опции для подключенного аккаунта */}
                {hhStatus?.is_connected && (
                  <Link
                    to="/profile"
                    className="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-500"
                  >
                    Управление аккаунтом
                    <ExternalLink className="w-4 h-4 ml-1" />
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage