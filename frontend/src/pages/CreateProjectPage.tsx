import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  CheckCircle, 
  AlertTriangle, 
  Upload, 
  Link as LinkIcon,
  ArrowRight,
  ArrowLeft,
  Settings,
  Home
} from 'lucide-react'
import { apiClient } from '../lib/api'
import { AIToolsList } from '../components/ai/AIToolsList'
import type { SessionInitResponse } from '../types/api'

interface HHStatus {
  is_connected: boolean
  expires_in_seconds?: number
  connected_at?: number
}

interface WizardState {
  currentStep: number
  resumeFile: File | null
  vacancyUrl: string
  isLoading: boolean
  error: string | null
  session: SessionInitResponse | null
}

const CreateProjectPage = () => {
  const navigate = useNavigate()
  const [hhStatus, setHhStatus] = useState<HHStatus | null>(null)
  const [hhLoading, setHhLoading] = useState(true)
  const [wizardState, setWizardState] = useState<WizardState>({
    currentStep: 1,
    resumeFile: null,
    vacancyUrl: '',
    isLoading: false,
    error: null,
    session: null
  })

  // Проверка HH статуса при загрузке
  useEffect(() => {
    const checkHHStatus = async () => {
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
    checkHHStatus()
  }, [])

  const handleHHConnect = async () => {
    try {
      await apiClient.connectToHH()
    } catch (error: any) {
      // Обработка 409 - уже подключен
      if (error.response?.status === 409) {
        setHhStatus({ is_connected: true })
        return
      }
      console.error('Failed to connect to HH:', error)
    }
  }

  const validateVacancyUrl = (url: string): boolean => {
    const hhUrlRegex = /hh\.ru\/vacancy\/\d+/
    return hhUrlRegex.test(url)
  }

  const handleFileSelect = (file: File) => {
    if (file.type !== 'application/pdf') {
      setWizardState(prev => ({ 
        ...prev, 
        error: 'Пожалуйста, выберите PDF файл' 
      }))
      return
    }
    setWizardState(prev => ({ 
      ...prev, 
      resumeFile: file, 
      error: null 
    }))
  }

  const handleCreateSession = async () => {
    if (!wizardState.resumeFile || !wizardState.vacancyUrl) {
      setWizardState(prev => ({ 
        ...prev, 
        error: 'Пожалуйста, загрузите резюме и укажите URL вакансии' 
      }))
      return
    }

    if (!validateVacancyUrl(wizardState.vacancyUrl)) {
      setWizardState(prev => ({ 
        ...prev, 
        error: 'Пожалуйста, введите корректный URL вакансии с hh.ru' 
      }))
      return
    }

    setWizardState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const formData = new FormData()
      formData.append('resume_file', wizardState.resumeFile)
      formData.append('vacancy_url', wizardState.vacancyUrl)
      formData.append('reuse_by_hash', 'true')

      const session = await apiClient.initSession(formData)
      
      setWizardState(prev => ({ 
        ...prev, 
        session,
        currentStep: 4,
        isLoading: false 
      }))

    } catch (error: any) {
      setWizardState(prev => ({ 
        ...prev, 
        isLoading: false,
        error: error.message || 'Не удалось создать проект' 
      }))
    }
  }

  const canProceedToStep3 = wizardState.resumeFile && wizardState.vacancyUrl && validateVacancyUrl(wizardState.vacancyUrl)

  const handleAIToolClick = (toolId: string) => {
    if (wizardState.session) {
      // TODO: Navigate to specific AI tool page
      console.log(`Navigate to AI tool: ${toolId} with session: ${wizardState.session.session_id}`)
      // navigate(`/project/${wizardState.session.session_id}/tools/${toolId}`)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          🚀 Создать новый проект
        </h1>
        <p className="text-lg text-gray-600">
          Загрузите резюме и укажите вакансию для персонализированного анализа
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex justify-center">
        <div className="flex items-center space-x-8">
          {[
            { num: 1, title: 'HH.ru', desc: 'Подключение' },
            { num: 2, title: 'Документы', desc: 'Загрузка' },
            { num: 3, title: 'Обработка', desc: 'Создание проекта' },
            { num: 4, title: 'Готово', desc: 'Переход к AI' }
          ].map((step, index) => (
            <div key={step.num} className="flex items-center">
              <div className="flex flex-col items-center">
                <div className={`
                  w-10 h-10 rounded-full flex items-center justify-center font-medium text-sm
                  ${wizardState.currentStep >= step.num
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-200 text-gray-500'
                  }
                `}>
                  {wizardState.currentStep > step.num ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : (
                    step.num
                  )}
                </div>
                <div className="mt-2 text-center">
                  <div className="text-sm font-medium text-gray-900">{step.title}</div>
                  <div className="text-xs text-gray-500">{step.desc}</div>
                </div>
              </div>
              {index < 3 && (
                <ArrowRight className="w-6 h-6 text-gray-300 mx-4" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Content based on current step */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        {/* Step 1: HH Connection Check */}
        {wizardState.currentStep === 1 && (
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center">
                <Settings className="w-10 h-10 text-indigo-600" />
              </div>
            </div>
            
            <div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Проверка подключения HH.ru
              </h2>
              <p className="text-gray-600 mb-6">
                Для создания проекта необходимо подключение к вашему HH.ru аккаунту
              </p>
            </div>

            {hhLoading ? (
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {hhStatus?.is_connected ? (
                  <>
                    <div className="flex items-center justify-center space-x-2 text-green-600">
                      <CheckCircle className="w-6 h-6" />
                      <span className="font-medium">HH.ru успешно подключен</span>
                    </div>
                    <button
                      onClick={() => setWizardState(prev => ({ ...prev, currentStep: 2 }))}
                      className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                    >
                      Продолжить
                      <ArrowRight className="ml-2 w-5 h-5" />
                    </button>
                  </>
                ) : (
                  <>
                    <div className="flex items-center justify-center space-x-2 text-red-600">
                      <AlertTriangle className="w-6 h-6" />
                      <span className="font-medium">HH.ru не подключен</span>
                    </div>
                    <button
                      onClick={handleHHConnect}
                      className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                    >
                      <Settings className="mr-2 w-5 h-5" />
                      Подключить HH.ru
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {/* Step 2: Document Upload */}
        {wizardState.currentStep === 2 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-900 text-center mb-8">
              Загрузка документов
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Resume Upload */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Upload className="w-5 h-5 mr-2" />
                  Резюме (PDF)
                </h3>
                
                <div className={`
                  border-2 border-dashed border-gray-300 rounded-lg p-6 text-center
                  ${wizardState.resumeFile ? 'border-green-300 bg-green-50' : 'hover:border-gray-400'}
                  transition-colors cursor-pointer
                `}>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) handleFileSelect(file)
                    }}
                    className="hidden"
                    id="resume-upload"
                  />
                  <label htmlFor="resume-upload" className="cursor-pointer">
                    {wizardState.resumeFile ? (
                      <div className="space-y-2">
                        <CheckCircle className="w-8 h-8 text-green-600 mx-auto" />
                        <p className="text-green-600 font-medium">{wizardState.resumeFile.name}</p>
                        <p className="text-sm text-gray-500">
                          {(wizardState.resumeFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="w-8 h-8 text-gray-400 mx-auto" />
                        <p className="text-gray-600">Нажмите или перетащите файл</p>
                        <p className="text-sm text-gray-500">PDF, до 10MB</p>
                      </div>
                    )}
                  </label>
                </div>
              </div>

              {/* Vacancy URL */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <LinkIcon className="w-5 h-5 mr-2" />
                  URL вакансии
                </h3>
                
                <div className="space-y-2">
                  <input
                    type="url"
                    value={wizardState.vacancyUrl}
                    onChange={(e) => setWizardState(prev => ({ 
                      ...prev, 
                      vacancyUrl: e.target.value,
                      error: null
                    }))}
                    placeholder="https://hh.ru/vacancy/123456789"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  
                  {wizardState.vacancyUrl && (
                    <div className="flex items-center space-x-2">
                      {validateVacancyUrl(wizardState.vacancyUrl) ? (
                        <>
                          <CheckCircle className="w-5 h-5 text-green-500" />
                          <span className="text-sm text-green-600">Корректный URL</span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="w-5 h-5 text-red-500" />
                          <span className="text-sm text-red-600">Некорректный URL HH.ru</span>
                        </>
                      )}
                    </div>
                  )}
                </div>

                <p className="text-sm text-gray-500">
                  Скопируйте ссылку на интересующую вас вакансию с сайта hh.ru
                </p>
              </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between pt-6">
              <button
                onClick={() => setWizardState(prev => ({ ...prev, currentStep: 1 }))}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
              >
                <ArrowLeft className="mr-2 w-5 h-5" />
                Назад
              </button>
              
              <button
                onClick={() => setWizardState(prev => ({ ...prev, currentStep: 3 }))}
                disabled={!canProceedToStep3}
                className={`
                  inline-flex items-center px-6 py-2 border border-transparent text-base font-medium rounded-md transition-colors
                  ${canProceedToStep3
                    ? 'text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
                    : 'text-gray-400 bg-gray-200 cursor-not-allowed'
                  }
                `}
              >
                Создать проект
                <ArrowRight className="ml-2 w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Processing */}
        {wizardState.currentStep === 3 && (
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center">
                {wizardState.isLoading ? (
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
                ) : (
                  <CheckCircle className="w-10 h-10 text-indigo-600" />
                )}
              </div>
            </div>
            
            <div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                {wizardState.isLoading ? 'Создание проекта...' : 'Готово к созданию'}
              </h2>
              <p className="text-gray-600">
                {wizardState.isLoading 
                  ? 'Парсим резюме и загружаем вакансию. Это может занять несколько секунд.'
                  : 'Нажмите "Создать", чтобы начать обработку документов'
                }
              </p>
            </div>

            {!wizardState.isLoading && (
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Резюме:</span>
                    <span className="text-sm font-medium">{wizardState.resumeFile?.name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Вакансия:</span>
                    <span className="text-sm font-medium text-blue-600 truncate ml-2" title={wizardState.vacancyUrl}>
                      {wizardState.vacancyUrl}
                    </span>
                  </div>
                </div>

                <div className="flex justify-center space-x-4">
                  <button
                    onClick={() => setWizardState(prev => ({ ...prev, currentStep: 2 }))}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                  >
                    <ArrowLeft className="mr-2 w-5 h-5" />
                    Изменить
                  </button>
                  
                  <button
                    onClick={handleCreateSession}
                    className="inline-flex items-center px-6 py-2 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                  >
                    Создать проект
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 4: Success + AI Tools */}
        {wizardState.currentStep === 4 && wizardState.session && (
          <div className="space-y-8">
            {/* Success Header */}
            <div className="text-center space-y-6">
              <div className="flex justify-center">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="w-10 h-10 text-green-600" />
                </div>
              </div>
              
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                  🎉 Проект успешно создан!
                </h2>
                <p className="text-gray-600">
                  Теперь выберите AI инструмент для анализа ваших документов
                </p>
              </div>

              {/* Project Info */}
              <div className="bg-green-50 rounded-lg p-4 space-y-2 max-w-2xl mx-auto">
                <div className="text-sm text-green-800">
                  <div><strong>Резюме:</strong> {wizardState.session.resume.title}</div>
                  <div><strong>Вакансия:</strong> {wizardState.session.vacancy.name}</div>
                  <div><strong>Компания:</strong> {wizardState.session.vacancy.company_name}</div>
                  {wizardState.session.reused.resume && (
                    <div className="text-xs text-green-600 mt-2">
                      ♻️ Резюме загружено из кэша
                    </div>
                  )}
                  {wizardState.session.reused.vacancy && (
                    <div className="text-xs text-green-600">
                      ♻️ Вакансия загружена из кэша
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* AI Tools Section */}
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  🤖 Выберите AI инструмент
                </h3>
                <p className="text-gray-600">
                  Кликните на любой инструмент, чтобы начать анализ
                </p>
              </div>

              <AIToolsList
                sessionId={wizardState.session.session_id}
                onToolClick={handleAIToolClick}
                showAsButtons={true}
                className="max-w-4xl mx-auto"
              />
            </div>

            {/* Bottom Navigation */}
            <div className="flex justify-between items-center pt-6 border-t border-gray-200">
              <button
                onClick={() => setWizardState(prev => ({ ...prev, currentStep: 2 }))}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
              >
                <ArrowLeft className="mr-2 w-5 h-5" />
                Создать другой проект
              </button>
              
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
              >
                <Home className="mr-2 w-5 h-5" />
                На главную
              </button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {wizardState.error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-400 mr-2" />
              <span className="text-red-800">{wizardState.error}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CreateProjectPage