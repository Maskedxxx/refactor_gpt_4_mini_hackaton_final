// frontend/tests/pages/AuthPage.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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

describe('AuthPage', () => {
  const mockApiClient = vi.mocked(api.apiClient)

  beforeEach(() => {
    vi.clearAllMocks()
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

  it('should show success message after successful login', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      user: { id: 1, email: 'test@example.com' },
      message: 'Успешный вход'
    }
    mockApiClient.login.mockResolvedValue(mockResponse)

    render(<AuthPage />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('✅ Успешно!')).toBeInTheDocument()
      expect(screen.getByText('Вы успешно вошли в систему.')).toBeInTheDocument()
    })

    // Form should be hidden
    expect(screen.queryByLabelText('Email')).not.toBeInTheDocument()
  })

  it('should show success message after successful signup', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      user: { id: 1, email: 'test@example.com', org_name: 'Test Org' },
      message: 'Пользователь создан'
    }
    mockApiClient.signup.mockResolvedValue(mockResponse)

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
      expect(screen.getByText('✅ Успешно!')).toBeInTheDocument()
      expect(screen.getByText('Аккаунт создан и вы авторизованы.')).toBeInTheDocument()
    })

    // Form should be hidden
    expect(screen.queryByLabelText('Email')).not.toBeInTheDocument()
  })

  it('should maintain form mode in success message', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      user: { id: 1, email: 'test@example.com' },
      message: 'Успешный вход'
    }
    mockApiClient.login.mockResolvedValue(mockResponse)

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
      expect(screen.getByText('Вы успешно вошли в систему.')).toBeInTheDocument()
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