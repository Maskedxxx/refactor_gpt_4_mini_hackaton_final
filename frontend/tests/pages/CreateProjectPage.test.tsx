// frontend/tests/pages/CreateProjectPage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CreateProjectPage from '../../src/pages/CreateProjectPage'

// Mock API client used by CreateProjectPage
vi.mock('../../src/lib/api', () => ({
  apiClient: {
    getHHStatus: vi.fn(),
    connectToHH: vi.fn(),
    initSession: vi.fn(),
    getFeatures: vi.fn(),
  },
}))

// Mock useNavigate to assert redirects without full app router
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import * as api from '../../src/lib/api'

describe('CreateProjectPage (wizard flow)', () => {
  const mockApi = vi.mocked(api.apiClient)

  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  it('submits correct FormData to initSession', async () => {
    const user = userEvent.setup()
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: true } as any)
    let capturedFormData: any = null
    mockApi.initSession.mockImplementationOnce(async (fd: any) => {
      capturedFormData = fd
      return {
        session_id: 'sess-x',
        resume: { title: 'T' },
        vacancy: { name: 'V', company_name: 'C' },
        reused: { resume: false, vacancy: false },
      } as any
    })

    const { container } = render(<CreateProjectPage />)

    // Step 1
    await screen.findByText('HH.ru успешно подключен')
    await user.click(screen.getByRole('button', { name: /Продолжить/i }))

    // Step 2
    const fileInput = container.querySelector('#resume-upload') as HTMLInputElement
    const pdf = new File([new Uint8Array([1, 2, 3])], 'resume.pdf', { type: 'application/pdf' })
    fireEvent.change(fileInput, { target: { files: [pdf] } })
    const urlInput = screen.getByPlaceholderText('https://hh.ru/vacancy/123456789') as HTMLInputElement
    await user.type(urlInput, 'https://hh.ru/vacancy/123456')
    await user.click(screen.getByRole('button', { name: /^Создать проект$/i }))

    // Step 3
    await screen.findByText('Готово к созданию')
    await user.click(screen.getByRole('button', { name: /^Создать проект$/i }))

    // Assert FormData content
    expect(capturedFormData).toBeInstanceOf(FormData)
    const resumeFile = capturedFormData.get('resume_file') as File
    expect(resumeFile).toBeInstanceOf(File)
    expect(resumeFile.name).toBe('resume.pdf')
    expect((resumeFile as any).type).toBe('application/pdf')
    expect(capturedFormData.get('vacancy_url')).toBe('https://hh.ru/vacancy/123456')
    expect(capturedFormData.get('reuse_by_hash')).toBe('true')
  })

  it('connectToHH non-409 error keeps UI on Step 1 (not connected)', async () => {
    const user = userEvent.setup()
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: false } as any)
    const err: any = new Error('Network')
    err.response = { status: 500 }
    mockApi.connectToHH.mockRejectedValueOnce(err)

    render(<CreateProjectPage />)
    await screen.findByText('HH.ru не подключен')
    await user.click(screen.getByRole('button', { name: /Подключить HH\.ru/i }))
    // Stays not connected
    expect(await screen.findByText('HH.ru не подключен')).toBeInTheDocument()
  })

  it('URL validation shows inline state and controls button availability', async () => {
    const user = userEvent.setup()
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: true } as any)
    const { container } = render(<CreateProjectPage />)

    await screen.findByText('HH.ru успешно подключен')
    await user.click(screen.getByRole('button', { name: /Продолжить/i }))

    const urlInput = screen.getByPlaceholderText('https://hh.ru/vacancy/123456789') as HTMLInputElement
    let proceedBtn = screen.getByRole('button', { name: /Создать проект/i })
    expect(proceedBtn).toBeDisabled()

    await user.type(urlInput, '   ')
    proceedBtn = screen.getByRole('button', { name: /Создать проект/i })
    expect(proceedBtn).toBeDisabled()
    expect(screen.queryByText(/Корректный URL/i)).not.toBeInTheDocument()

    await user.clear(urlInput)
    await user.type(urlInput, 'https://hh.ru/vacancy/987654')
    expect(await screen.findByText(/Корректный URL/i)).toBeInTheDocument()
  })

  it('spinners: Step 1 while loading status and Step 3 while creating', async () => {
    // Step 1: delay status to see spinner
    let resolveStatus: (v: any) => void
    const statusPromise = new Promise((r) => (resolveStatus = r))
    mockApi.getHHStatus.mockReturnValueOnce(statusPromise as any)

    const { container } = render(<CreateProjectPage />)
    // Spinner is a div with animate-spin class in Step 1
    const spinners = container.querySelectorAll('.animate-spin')
    expect(spinners.length).toBeGreaterThan(0)
    resolveStatus!({ is_connected: true })
    await screen.findByText('HH.ru успешно подключен')

    // Step 3: mock initSession pending to show spinner
    const user = userEvent.setup()
    mockApi.initSession.mockReturnValueOnce(new Promise(() => {}) as any)

    await user.click(screen.getByRole('button', { name: /Продолжить/i }))
    const fileInput = container.querySelector('#resume-upload') as HTMLInputElement
    const pdf = new File([new Uint8Array([1, 2, 3])], 'resume.pdf', { type: 'application/pdf' })
    fireEvent.change(fileInput, { target: { files: [pdf] } })
    const urlInput = screen.getByPlaceholderText('https://hh.ru/vacancy/123456789') as HTMLInputElement
    await user.type(urlInput, 'https://hh.ru/vacancy/123456')
    await user.click(screen.getByRole('button', { name: /^Создать проект$/i }))
    await screen.findByText('Готово к созданию')
    await user.click(screen.getByRole('button', { name: /^Создать проект$/i }))

    // Step 3 spinner visible
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })
  it('happy path: HH connected → upload → preview → create → success + tools', async () => {
    const user = userEvent.setup()
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: true } as any)

    // Mock session creation response
    mockApi.initSession.mockResolvedValueOnce({
      session_id: 'sess-123',
      resume: { title: 'Senior Python Developer' },
      vacancy: { name: 'Python Engineer', company_name: 'Acme Inc.' },
      reused: { resume: true, vacancy: false },
    } as any)

    const { container } = render(<CreateProjectPage />)

    // Step 1: HH check
    expect(screen.getByText('Проверка подключения HH.ru')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('HH.ru успешно подключен')).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /Продолжить/i }))

    // Step 2: Upload
    await waitFor(() => {
      expect(screen.getByText('Загрузка документов')).toBeInTheDocument()
    })
    const fileInput = container.querySelector('#resume-upload') as HTMLInputElement
    const pdf = new File([new Uint8Array([1, 2, 3])], 'resume.pdf', { type: 'application/pdf' })
    await user.upload(fileInput, pdf)
    const urlInput = screen.getByPlaceholderText('https://hh.ru/vacancy/123456789') as HTMLInputElement
    await user.type(urlInput, 'https://hh.ru/vacancy/123456')

    // Move to Step 3 (Preview/Processing)
    const proceedBtn = screen.getByRole('button', { name: /^Создать проект$/i })
    expect(proceedBtn).toBeEnabled()
    await user.click(proceedBtn)

    // Step 3: Preview and confirm create
    await waitFor(() => {
      expect(screen.getByText('Готово к созданию')).toBeInTheDocument()
    })
    expect(screen.getByText('resume.pdf')).toBeInTheDocument()
    expect(screen.getByText('https://hh.ru/vacancy/123456')).toBeInTheDocument()
    const createBtn = screen.getByRole('button', { name: /^Создать проект$/i })
    await user.click(createBtn)

    // After API resolves → Step 4: Success + AI tools
    await waitFor(() => {
      expect(screen.getByText(/Проект успешно создан!/i)).toBeInTheDocument()
    })
    expect(screen.getByText('Senior Python Developer')).toBeInTheDocument()
    expect(screen.getByText('Python Engineer')).toBeInTheDocument()
    expect(screen.getByText('Acme Inc.')).toBeInTheDocument()
    // Reuse indicator for resume
    expect(screen.getByText(/Резюме загружено из кэша/)).toBeInTheDocument()

    // Clicking an AI tool triggers log (current implementation)
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    await user.click(screen.getByRole('button', { name: /Cover Letter/i }))
    expect(logSpy).toHaveBeenCalledWith(expect.stringContaining('Navigate to AI tool: cover_letter'))
    logSpy.mockRestore()

    // Navigate back to dashboard
    await user.click(screen.getByRole('button', { name: /На главную/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('handles disconnected HH with 409 already connected on connect flow', async () => {
    const user = userEvent.setup()
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: false } as any)

    const conflict: any = new Error('Conflict')
    conflict.response = { status: 409 }
    mockApi.connectToHH.mockRejectedValueOnce(conflict)

    render(<CreateProjectPage />)

    await waitFor(() => {
      expect(screen.getByText('HH.ru не подключен')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Подключить HH\.ru/i }))
    await waitFor(() => {
      expect(screen.getByText('HH.ru успешно подключен')).toBeInTheDocument()
    })
  })

  it('validates file type and URL correctness on Step 2', async () => {
    const user = userEvent.setup()
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: true } as any)
    const { container } = render(<CreateProjectPage />)

    await waitFor(() => {
      expect(screen.getByText('HH.ru успешно подключен')).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /Продолжить/i }))

    // Invalid file
    const fileInput = container.querySelector('#resume-upload') as HTMLInputElement
    const txt = new File([new Uint8Array([1, 2, 3])], 'note.txt', { type: 'text/plain' })
    // Для скрытого input используем прямой change, чтобы гарантированно сработал onChange
    fireEvent.change(fileInput, { target: { files: [txt] } })
    await screen.findByText(/Пожалуйста,\s*выберите\s*PDF\s*файл/i)

    // Valid file removes error when url also valid later
    const pdf = new File([new Uint8Array([1, 2, 3])], 'resume.pdf', { type: 'application/pdf' })
    fireEvent.change(fileInput, { target: { files: [pdf] } })
    // после валидного файла ошибка должна исчезнуть
    await waitFor(() => {
      expect(screen.queryByText(/Пожалуйста,\s*выберите\s*PDF\s*файл/i)).not.toBeInTheDocument()
    })
    const urlInput = screen.getByPlaceholderText('https://hh.ru/vacancy/123456789') as HTMLInputElement
    await user.type(urlInput, 'https://example.com/not-hh')
    expect(screen.getByText(/Некорректный URL HH\.ru/)).toBeInTheDocument()

    // Button disabled until valid
    let proceedBtn = screen.getByRole('button', { name: /Создать проект/i })
    expect(proceedBtn).toBeDisabled()

    // Fix URL → valid
    await user.clear(urlInput)
    await user.type(urlInput, 'https://hh.ru/vacancy/987654')
    expect(await screen.findByText(/Корректный URL/)).toBeInTheDocument()
    // Перечитываем кнопку, чтобы избежать устаревшей ссылки
    proceedBtn = screen.getByRole('button', { name: /Создать проект/i })
    await waitFor(() => expect(proceedBtn).toBeEnabled())
  })

  it('shows error message when initSession fails', async () => {
    const user = userEvent.setup()
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: true } as any)
    mockApi.initSession.mockRejectedValueOnce(new Error('Не удалось создать проект'))

    const { container } = render(<CreateProjectPage />)

    await waitFor(() => {
      expect(screen.getByText('HH.ru успешно подключен')).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /Продолжить/i }))

    const fileInput = container.querySelector('#resume-upload') as HTMLInputElement
    const pdf = new File([new Uint8Array([1, 2, 3])], 'resume.pdf', { type: 'application/pdf' })
    await user.upload(fileInput, pdf)
    const urlInput = screen.getByPlaceholderText('https://hh.ru/vacancy/123456789') as HTMLInputElement
    await user.type(urlInput, 'https://hh.ru/vacancy/123456')

    // Go to Step 3
    await user.click(screen.getByRole('button', { name: /Создать проект/i }))

    // Click create to trigger initSession error
    await waitFor(() => {
      expect(screen.getByText('Готово к созданию')).toBeInTheDocument()
    })
    await user.click(screen.getAllByRole('button', { name: /Создать проект/i })[0])

    await waitFor(() => {
      expect(screen.getByText(/Не удалось создать проект/)).toBeInTheDocument()
    })
  })
})
