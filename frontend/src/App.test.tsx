import { fireEvent, render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import App from './App'

vi.mock('./components/MapView', () => ({ default: () => <div data-testid="map" /> }))

describe('App', () => {
  it('renders the required trip inputs', () => {
    render(<App />)
    expect(screen.getByLabelText('Current location')).toBeInTheDocument()
    expect(screen.getByLabelText('Pickup location')).toBeInTheDocument()
    expect(screen.getByLabelText('Drop-off location')).toBeInTheDocument()
    expect(screen.getByRole('spinbutton', { name: /Cycle used/i })).toBeInTheDocument()
  })

  it('shows API validation failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: 'Route unavailable' }) }))
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Plan compliant trip' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Route unavailable')
  })
})
