import { 
  FileText, 
  BarChart3, 
  ClipboardList, 
  Users 
} from 'lucide-react'

export interface AITool {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  color: string
}

// Список AI инструментов - синхронизирован с Dashboard и Backend
export const AI_TOOLS: AITool[] = [
  {
    id: 'cover_letter',
    name: 'Cover Letter',
    description: 'Генерация персонализированных сопроводительных писем',
    icon: <FileText className="w-6 h-6" />,
    color: 'text-blue-600'
  },
  {
    id: 'gap_analyzer', 
    name: 'Gap Analyzer',
    description: 'Анализ соответствия резюме вакансии',
    icon: <BarChart3 className="w-6 h-6" />,
    color: 'text-green-600'
  },
  {
    id: 'interview_checklist',
    name: 'Interview Checklist', 
    description: 'Подготовка к собеседованию',
    icon: <ClipboardList className="w-6 h-6" />,
    color: 'text-purple-600'
  },
  {
    id: 'interview_simulation',
    name: 'Interview Simulation',
    description: 'Симуляция собеседования',
    icon: <Users className="w-6 h-6" />,
    color: 'text-orange-600'
  }
]

interface AIToolsListProps {
  sessionId?: string
  onToolClick?: (toolId: string) => void
  showAsButtons?: boolean
  className?: string
}

export const AIToolsList = ({ 
  sessionId, 
  onToolClick, 
  showAsButtons = false,
  className = ""
}: AIToolsListProps) => {
  const handleToolClick = (toolId: string) => {
    if (onToolClick) {
      onToolClick(toolId)
    } else {
      console.log(`AI Tool clicked: ${toolId}, session: ${sessionId}`)
    }
  }

  if (showAsButtons) {
    return (
      <div className={`grid grid-cols-1 sm:grid-cols-2 gap-4 ${className}`}>
        {AI_TOOLS.map((tool) => (
          <button
            key={tool.id}
            onClick={() => handleToolClick(tool.id)}
            className="flex items-start p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-all group text-left focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <div className={`${tool.color} mt-1 flex-shrink-0 group-hover:scale-110 transition-transform`}>
              {tool.icon}
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-gray-900 group-hover:text-indigo-900">
                {tool.name}
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                {tool.description}
              </p>
            </div>
          </button>
        ))}
      </div>
    )
  }

  // Preview mode (как на Dashboard)
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 gap-4 ${className}`}>
      {AI_TOOLS.map((tool) => (
        <div key={tool.id} className="flex items-start p-4 border border-gray-200 rounded-lg">
          <div className={`${tool.color} mt-1 flex-shrink-0`}>
            {tool.icon}
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-gray-900">{tool.name}</h3>
            <p className="text-sm text-gray-500 mt-1">
              {tool.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}