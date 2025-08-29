// frontend/tests/pages/AuthPage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthPage } from '../../src/pages/AuthPage'
import * as api from '../../src/lib/api'

// Mock API client
vi.mock('../../src/lib/api', () => ({
  apiClient: {
    login: vi.fn(),
    signup: vi.fn()
  }
}))

// Mock useNavigate to avoid Router context and to assert redirects
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('AuthPage', () => {
  const mockApiClient = vi.mocked(api.apiClient)

  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  it('should render with login form by default', () => {
    render(<AuthPage />)

    expect(screen.getByText('HR Assistant')).toBeInTheDocument()
    expect(screen.getByText('Система для работы с резюме и вакансиями')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Вход' })).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Пароль')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Войти' })).toBeInTheDocument()
  })

  it('should switch to signup form when clicking "Регистрация"', async () => {
    const user = userEvent.setup()
    render(<AuthPage />)

    const signupTab = screen.getByRole('button', { name: 'Регистрация' })
    await user.click(signupTab)

    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Пароль')).toBeInTheDocument()
    expect(screen.getByLabelText('Название организации')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Создать аккаунт' })).toBeInTheDocument()
  })

  it('should switch back to login form when clicking "Вход"', async () => {
    const user = userEvent.setup()
    render(<AuthPage />)

    // Switch to signup
    await user.click(screen.getByRole('button', { name: 'Регистрация' }))
    expect(screen.getByRole('button', { name: 'Создать аккаунт' })).toBeInTheDocument()

    // Switch back to login
    await user.click(screen.getByRole('button', { name: 'Вход' }))
    expect(screen.getByRole('button', { name: 'Войти' })).toBeInTheDocument()
  })

  it('should navigate to /dashboard after successful login', async () => {
    const user = userEvent.setup()
    mockApiClient.login.mockResolvedValue({ user: { id: 1 }, message: 'ok' } as any)

    render(<AuthPage />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockApiClient.login).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('should navigate to /dashboard after successful signup', async () => {
    const user = userEvent.setup()
    mockApiClient.signup.mockResolvedValue({ user: { id: 1 }, message: 'created' } as any)

    render(<AuthPage />)

    // Switch to signup form
    await user.click(screen.getByRole('button', { name: 'Регистрация' }))

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')
    const submitButton = screen.getByRole('button', { name: 'Создать аккаунт' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(orgNameInput, 'Test Organization')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockApiClient.signup).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('should keep active tab styling before redirect on login', async () => {
    const user = userEvent.setup()
    mockApiClient.login.mockResolvedValue({ user: { id: 1 } } as any)

    render(<AuthPage />)

    // Ensure we're in login mode
    expect(screen.getByRole('button', { name: 'Вход' })).toHaveClass('bg-white')

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('should show correct title for login mode', () => {
    render(<AuthPage />)
    
    expect(screen.getByRole('button', { name: 'Вход' })).toHaveClass('bg-white')
    expect(screen.getByRole('button', { name: 'Регистрация' })).not.toHaveClass('bg-white')
  })

  it('should show correct title for signup mode', async () => {
    const user = userEvent.setup()
    render(<AuthPage />)

    await user.click(screen.getByRole('button', { name: 'Регистрация' }))

    expect(screen.getByRole('button', { name: 'Регистрация' })).toHaveClass('bg-white')
    expect(screen.getByRole('button', { name: 'Вход' })).not.toHaveClass('bg-white')
  })

  it('should render page header and description consistently', () => {
    render(<AuthPage />)

    expect(screen.getByText('HR Assistant')).toBeInTheDocument()
    expect(screen.getByText('Система для работы с резюме и вакансиями')).toBeInTheDocument()
  })
})
