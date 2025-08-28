// frontend/tests/components/auth/SignupForm.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SignupForm } from '../../../src/components/auth/SignupForm'
import * as api from '../../../src/lib/api'

// Mock API client
vi.mock('../../../src/lib/api', () => ({
  apiClient: {
    signup: vi.fn()
  }
}))

describe('SignupForm', () => {
  const mockOnSuccess = vi.fn()
  const mockApiClient = vi.mocked(api.apiClient)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render signup form with all fields', () => {
    render(<SignupForm onSuccess={mockOnSuccess} />)

    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Пароль')).toBeInTheDocument()
    expect(screen.getByLabelText('Название организации')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Создать аккаунт' })).toBeInTheDocument()
  })

  it('should update input values when user types', async () => {
    const user = userEvent.setup()
    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement
    const passwordInput = screen.getByLabelText('Пароль') as HTMLInputElement
    const orgNameInput = screen.getByLabelText('Название организации') as HTMLInputElement

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(orgNameInput, 'Test Organization')

    expect(emailInput.value).toBe('test@example.com')
    expect(passwordInput.value).toBe('password123')
    expect(orgNameInput.value).toBe('Test Organization')
  })

  it('should prevent submission with empty fields (HTML5 validation)', async () => {
    const user = userEvent.setup()
    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')
    const submitButton = screen.getByRole('button', { name: 'Создать аккаунт' })

    // HTML5 validation prevents form submission if required fields are empty
    await user.click(submitButton)

    // Form should still be present (not submitted)
    expect(emailInput).toBeInTheDocument()
    expect(passwordInput).toBeInTheDocument()
    expect(orgNameInput).toBeInTheDocument()
    expect(mockOnSuccess).not.toHaveBeenCalled()
  })

  it('should prevent submission with invalid email (HTML5 validation)', async () => {
    const user = userEvent.setup()
    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')
    const submitButton = screen.getByRole('button', { name: 'Создать аккаунт' })

    await user.type(emailInput, 'invalid-email')
    await user.type(passwordInput, 'password123')
    await user.type(orgNameInput, 'Test Org')
    await user.click(submitButton)

    // HTML5 validation prevents submission with invalid email
    expect(mockOnSuccess).not.toHaveBeenCalled()
  })

  it('should prevent submission with short password (HTML5 minlength validation)', async () => {
    const user = userEvent.setup()
    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')
    const submitButton = screen.getByRole('button', { name: 'Создать аккаунт' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, '123')
    await user.type(orgNameInput, 'Test Org')
    await user.click(submitButton)

    // HTML5 minlength validation prevents submission
    expect(mockOnSuccess).not.toHaveBeenCalled()
  })

  it('should allow submission with short org_name (no client-side length validation)', async () => {
    const user = userEvent.setup()
    mockApiClient.signup.mockResolvedValue({ message: 'Success' })
    
    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(orgNameInput, 'AB') // Short org_name
    await user.click(screen.getByRole('button', { name: 'Создать аккаунт' }))

    // Verify API was called with short org_name (no client-side validation blocked it)
    await waitFor(() => {
      expect(mockApiClient.signup).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        org_name: 'AB'
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
      user: { id: 1, email: 'test@example.com', org_name: 'Test Organization' },
      message: 'Пользователь создан'
    }
    mockApiClient.signup.mockResolvedValue(mockResponse)

    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')
    const submitButton = screen.getByRole('button', { name: 'Создать аккаунт' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(orgNameInput, 'Test Organization')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockApiClient.signup).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        org_name: 'Test Organization'
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
    mockApiClient.signup.mockReturnValue(mockPromise)

    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')
    const submitButton = screen.getByRole('button', { name: 'Создать аккаунт' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(orgNameInput, 'Test Organization')
    await user.click(submitButton)

    expect(screen.getByText('Регистрация...')).toBeInTheDocument()
    expect(submitButton).toBeDisabled()

    // Resolve the promise to clean up
    resolvePromise!({ user: {}, message: 'Success' })
  })

  it('should show error message when signup fails', async () => {
    const user = userEvent.setup()
    // Mock signup to reject with error and make sure it stays rejected
    mockApiClient.signup.mockRejectedValueOnce(new Error('Пользователь уже существует'))

    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')
    const submitButton = screen.getByRole('button', { name: 'Создать аккаунт' })

    await user.type(emailInput, 'existing@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(orgNameInput, 'Test Organization')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Пользователь уже существует')).toBeInTheDocument()
    })

    expect(mockOnSuccess).not.toHaveBeenCalled()
  })

  it('should clear error message when user starts typing', async () => {
    const user = userEvent.setup()
    mockApiClient.signup.mockRejectedValue(new Error('Пользователь уже существует'))

    render(<SignupForm onSuccess={mockOnSuccess} />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Пароль')
    const orgNameInput = screen.getByLabelText('Название организации')
    const submitButton = screen.getByRole('button', { name: 'Создать аккаунт' })

    // Trigger error
    await user.type(emailInput, 'existing@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(orgNameInput, 'Test Organization')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Пользователь уже существует')).toBeInTheDocument()
    })

    // Start typing again
    await user.type(emailInput, 'a')

    expect(screen.queryByText('Пользователь уже существует')).not.toBeInTheDocument()
  })
})