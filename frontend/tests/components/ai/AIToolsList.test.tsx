// frontend/tests/components/ai/AIToolsList.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AIToolsList } from '../../../src/components/ai/AIToolsList'

describe('AIToolsList', () => {
  it('renders 4 preview cards by default', () => {
    render(<AIToolsList />)
    expect(screen.getByText('Cover Letter')).toBeInTheDocument()
    expect(screen.getByText('Gap Analyzer')).toBeInTheDocument()
    expect(screen.getByText('Interview Checklist')).toBeInTheDocument()
    expect(screen.getByText('Interview Simulation')).toBeInTheDocument()
  })

  it('calls onToolClick with tool id in interactive mode', async () => {
    const user = userEvent.setup()
    const onToolClick = vi.fn()
    render(<AIToolsList showAsButtons={true} onToolClick={onToolClick} sessionId="sess-1" />)

    await user.click(screen.getByRole('button', { name: /Cover Letter/i }))
    expect(onToolClick).toHaveBeenCalledWith('cover_letter')
  })
})

