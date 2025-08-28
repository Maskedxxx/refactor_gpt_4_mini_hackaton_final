// frontend/tests/components/auth/LoginForm.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginForm } from '../../../src/components/auth/LoginForm'
import * as api from '../../../src/lib/api'

// Mock API client
vi.mock('../../../src/lib/api', () => ({
  apiClient: {
    login: vi.fn()
  }
}))

describe('LoginForm', () => {
  const mockOnSuccess = vi.fn()
  const mockApiClient = vi.mocked(api.apiClient)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render login form with all fields', () => {
    render(<LoginForm onSuccess={mockOnSuccess} />)

    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Пароль')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Войти' })).toBeInTheDocument()
  })

  it('should update input values when user types', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement
    const passwordInput = screen.getByLabelText('Пароль') as HTMLInputElement

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    expect(emailInput.value).toBe('test@example.com')
    expect(passwordInput.value).toBe('password123')
  })

  it('should prevent submission with empty fields (HTML5 validation)', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    // HTML5 validation prevents form submission if required fields are empty
    await user.click(submitButton)

    // Form should still be present (not submitted)
    expect(emailInput).toBeInTheDocument()
    expect(passwordInput).toBeInTheDocument()
    expect(mockOnSuccess).not.toHaveBeenCalled()
  })

  it('should prevent submission with invalid email (HTML5 validation)', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    await user.type(emailInput, 'invalid-email')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    // HTML5 validation prevents submission with invalid email
    expect(mockOnSuccess).not.toHaveBeenCalled()
  })

  it('should allow submission with short password (no client-side length validation)', async () => {
    const user = userEvent.setup()
    mockApiClient.login.mockResolvedValue({ message: 'Success' })
    
    render(<LoginForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, '123') // Short password
    await user.click(screen.getByRole('button', { name: 'Войти' }))

    // Verify API was called with short password (no client-side validation blocked it)
    await waitFor(() => {
      expect(mockApiClient.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: '123'
      })
    })
    
    // Verify success callback was called
    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('should submit form with valid data and call onSuccess', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      user: { id: 1, email: 'test@example.com' },
      message: 'Успешный вход'
    }
    mockApiClient.login.mockResolvedValue(mockResponse)

    render(<LoginForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockApiClient.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('should show loading state during submission', async () => {
    const user = userEvent.setup()
    let resolvePromise: (value: any) => void
    const mockPromise = new Promise<any>((resolve) => {
      resolvePromise = resolve
    })
    mockApiClient.login.mockReturnValue(mockPromise)

    render(<LoginForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    expect(screen.getByText('Вход...')).toBeInTheDocument()
    expect(submitButton).toBeDisabled()

    // Resolve the promise to clean up
    resolvePromise!({ user: {}, message: 'Success' })
  })

  it('should show error message when login fails', async () => {
    const user = userEvent.setup()
    // Clear previous mock behavior and set rejection
    mockApiClient.login.mockReset()
    mockApiClient.login.mockRejectedValueOnce(new Error('Неверный email или пароль'))

    render(<LoginForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText('Неверный email или пароль')).toBeInTheDocument()
    })

    // Wait a bit more to ensure any async operations complete
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(mockOnSuccess).not.toHaveBeenCalled()
  })

  it('should clear error message when user starts typing', async () => {
    const user = userEvent.setup()
    mockApiClient.login.mockRejectedValue(new Error('Неверный email или пароль'))

    render(<LoginForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const submitButton = screen.getByRole('button', { name: 'Войти' })

    // Trigger error
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Неверный email или пароль')).toBeInTheDocument()
    })

    // Start typing again - error should be cleared by onChange handler
    await user.type(emailInput, 'a')

    // Error message should be cleared
    expect(screen.queryByText('Неверный email или пароль')).not.toBeInTheDocument()
  })
})