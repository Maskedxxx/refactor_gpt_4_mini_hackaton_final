// frontend/tests/pages/DashboardPage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import DashboardPage from '../../src/pages/DashboardPage'

// Mock API client used by DashboardPage
vi.mock('../../src/lib/api', () => ({
  apiClient: {
    getHHStatus: vi.fn(),
    connectToHH: vi.fn(),
  },
}))

import * as api from '../../src/lib/api'

describe('DashboardPage (base)', () => {
  const mockApi = vi.mocked(api.apiClient)

  const renderWithRouter = () =>
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <DashboardPage />
      </MemoryRouter>
    )

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state before HH status resolves and then renders result', async () => {
    // Keep pending until first assertion, then resolve
    let resolveStatus: (v: any) => void
    const statusPromise = new Promise((resolve) => {
      resolveStatus = resolve
    })
    ;(mockApi.getHHStatus as any).mockReturnValueOnce(statusPromise)

    renderWithRouter()

    // While loading, refresh button (available only after load) should not be present
    expect(screen.queryByTitle('Обновить статус')).not.toBeInTheDocument()

    // Resolve and ensure content appears
    resolveStatus!({ is_connected: false })
    await waitFor(() => {
      expect(screen.getByText('Не подключен')).toBeInTheDocument()
    })
    // Refresh button appears after loading
    expect(screen.getByTitle('Обновить статус')).toBeInTheDocument()
  })

  it('renders connected state with email and disabled green button', async () => {
    mockApi.getHHStatus.mockResolvedValueOnce({
      is_connected: true,
      account_info: { email: 'user@example.com' },
    } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('Подключен')).toBeInTheDocument()
    })
    expect(screen.getByText('user@example.com')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /HH\.ru подключен/i })).toBeDisabled()
    // Link to profile is visible when connected
    expect(screen.getByRole('link', { name: /Управление аккаунтом/i })).toHaveAttribute('href', '/profile')
  })

  it('renders disconnected state with connect button and helper note', async () => {
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: false } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('Не подключен')).toBeInTheDocument()
    })
    const connectBtn = screen.getByRole('button', { name: /Подключить HH\.ru/i })
    expect(connectBtn).toBeInTheDocument()
    expect(
      screen.getByText(/После авторизации на HH\.ru статус обновится автоматически/i)
    ).toBeInTheDocument()
    // No profile link when disconnected
    expect(screen.queryByRole('link', { name: /Управление аккаунтом/i })).not.toBeInTheDocument()
  })

  it('manual refresh button triggers HH status re-fetch and updates UI', async () => {
    // First response: disconnected
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: false } as any)
    // Second response after refresh: connected
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: true } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('Не подключен')).toBeInTheDocument()
    })

    // Click refresh button (🔄)
    const refreshBtn = screen.getByTitle('Обновить статус')
    await userEvent.click(refreshBtn)

    await waitFor(() => {
      expect(screen.getByText('Подключен')).toBeInTheDocument()
    })
    expect(mockApi.getHHStatus).toHaveBeenCalledTimes(2)
  })

  it('connectToHH 409 already connected updates UI immediately and then refetches', async () => {
    // Initially disconnected
    mockApi.getHHStatus.mockResolvedValueOnce({ is_connected: false } as any)

    // connectToHH rejects with 409
    const conflictError: any = new Error('Conflict')
    conflictError.response = { status: 409, data: { detail: { error_code: 'HH_ALREADY_CONNECTED' } } }
    mockApi.connectToHH.mockRejectedValueOnce(conflictError)

    // After immediate UI switch, component triggers background refresh
    mockApi.getHHStatus.mockResolvedValueOnce({
      is_connected: true,
      account_info: { email: 'user@example.com' },
    } as any)

    renderWithRouter()

    // Wait until disconnected UI appears (connect button is a reliable marker)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Подключить HH\.ru/i })).toBeInTheDocument()
    })

    // Click connect
    const connectBtn = screen.getByRole('button', { name: /Подключить HH\.ru/i })
    await userEvent.click(connectBtn)

    // Immediate optimistic UI change
    await waitFor(() => {
      expect(screen.getByText('Подключен')).toBeInTheDocument()
    })

    // Background refresh called
    expect(mockApi.getHHStatus).toHaveBeenCalledTimes(2)
  })
})
