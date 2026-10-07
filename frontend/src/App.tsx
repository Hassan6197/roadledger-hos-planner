import { FormEvent, useMemo, useState } from 'react'
import EldLog from './components/EldLog'
import MapView from './components/MapView'
import Timeline from './components/Timeline'
import type { PlanResponse } from './types'

const example = {
  current_location: 'Chicago, IL',
  pickup_location: 'Omaha, NE',
  dropoff_location: 'Denver, CO',
  current_cycle_used: '12',
}

function toLocalInputValue(date: Date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 16)
}

function withTimezoneOffset(value: string) {
  const date = new Date(value)
  const offsetMinutes = -date.getTimezoneOffset()
  const sign = offsetMinutes >= 0 ? '+' : '-'
  const hours = String(Math.floor(Math.abs(offsetMinutes) / 60)).padStart(2, '0')
  const minutes = String(Math.abs(offsetMinutes) % 60).padStart(2, '0')
  return `${value}:00${sign}${hours}:${minutes}`
}

export default function App() {
  const [form, setForm] = useState({ ...example, departure_at: toLocalInputValue(new Date()) })
  const [result, setResult] = useState<PlanResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeView, setActiveView] = useState<'schedule' | 'directions'>('schedule')
  const [showAllDirections, setShowAllDirections] = useState(false)

  const trip = result?.trip
  const resetCount = useMemo(() => trip?.segments.filter((item) => ['sleeper', 'restart'].includes(item.kind)).length || 0, [trip])

  const update = (field: string, value: string) => setForm((current) => ({ ...current, [field]: value }))

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setShowAllDirections(false)
    try {
      const response = await fetch('/api/plan/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, departure_at: withTimezoneOffset(form.departure_at), current_cycle_used: Number(form.current_cycle_used) }),
      })
      const body = await response.json()
      if (!response.ok) throw new Error(body.error || 'The trip could not be planned.')
      setResult(body)
      requestAnimationFrame(() => document.getElementById('trip-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The trip could not be planned.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div id="top" className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="RoadLedger home">
          <span className="brand__mark"><i /></span>
          <span>RoadLedger</span>
        </a>
        <div className="topbar__rule"><i /> FMCSA property-carrying · 70 hr / 8 day</div>
      </header>

      <main>
        <section className="planner-grid" aria-labelledby="planner-title">
          <div className="planner-panel">
            <div className="planner-copy">
              <div className="eyebrow">HOS trip planner</div>
              <h1 id="planner-title">Plan the run.<br />Protect the clock.</h1>
              <p className="intro">A route, legal duty schedule, and ready-to-review daily logs—in one pass.</p>
            </div>
            <form onSubmit={submit} className="trip-form">
              <div className="form-heading"><strong>Trip details</strong><span>3 stops</span></div>
              <div className="route-fields">
                <div className="route-field">
                  <span className="route-node route-node--start">S</span>
                  <label htmlFor="current-location">
                    <span>Current location</span>
                    <input id="current-location" required value={form.current_location} onChange={(e) => update('current_location', e.target.value)} placeholder="City, state or ZIP" autoComplete="address-level2" />
                  </label>
                </div>
                <div className="route-field">
                  <span className="route-node route-node--pickup">P</span>
                  <label htmlFor="pickup-location">
                    <span>Pickup location</span>
                    <input id="pickup-location" required value={form.pickup_location} onChange={(e) => update('pickup_location', e.target.value)} placeholder="City, state or ZIP" autoComplete="address-level2" />
                  </label>
                </div>
                <div className="route-field">
                  <span className="route-node route-node--finish">D</span>
                  <label htmlFor="dropoff-location">
                    <span>Drop-off location</span>
                    <input id="dropoff-location" required value={form.dropoff_location} onChange={(e) => update('dropoff_location', e.target.value)} placeholder="City, state or ZIP" autoComplete="address-level2" />
                  </label>
                </div>
              </div>
              <div className="form-row">
                <label htmlFor="cycle-used">
                  <span>Cycle used <small>{Math.max(0, 70 - Number(form.current_cycle_used || 0))} hr available</small></span>
                  <div className="input-suffix"><input id="cycle-used" required type="number" min="0" max="70" step="0.5" value={form.current_cycle_used} onChange={(e) => update('current_cycle_used', e.target.value)} /><b>hrs</b></div>
                </label>
                <label htmlFor="departure-at">
                  <span>Depart</span>
                  <input id="departure-at" required type="datetime-local" value={form.departure_at} onChange={(e) => update('departure_at', e.target.value)} />
                </label>
              </div>
              {error && <div className="form-error" role="alert">{error}</div>}
              <button className="plan-button" disabled={loading} type="submit">
                {loading ? <><span className="spinner" /> Building legal route…</> : <><span>Plan compliant trip</span><b aria-hidden="true">→</b></>}
              </button>
              <p className="form-note"><span aria-hidden="true">✓</span> Checks 11-hour driving, 14-hour window, breaks, rests, and the 70-hour cycle.</p>
            </form>
          </div>
          <MapView trip={trip} loading={loading} />
        </section>

        {trip && (
          <div id="trip-results" className="results">
            <nav className="result-nav" aria-label="Trip results">
              <span><i /> Plan ready</span>
              <div>
                <a href="#trip-results">Overview</a>
                <a href="#schedule">Schedule</a>
                <a href="#daily-logs">Daily logs</a>
              </div>
            </nav>
            <section className="summary-strip" aria-label="Trip summary">
              <div><span>Route</span><strong>{trip.distance_miles.toLocaleString()} mi</strong></div>
              <div><span>Driving</span><strong>{trip.drive_hours} hr</strong></div>
              <div><span>Arrival</span><strong>{new Date(trip.arrival_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</strong></div>
              <div><span>Rest periods</span><strong>{resetCount}</strong></div>
              <div className="cycle-meter">
                <span>Cycle remaining</span>
                <strong>{trip.cycle.remaining} hr</strong>
                <i><b style={{ width: `${(trip.cycle.remaining / 70) * 100}%` }} /></i>
              </div>
            </section>

            <section id="schedule" className="plan-section">
              <div className="section-heading">
                <div><div className="eyebrow">Route plan</div><h2>Duty schedule</h2></div>
                <div className="segmented-control" role="group" aria-label="Plan view">
                  <button className={activeView === 'schedule' ? 'active' : ''} onClick={() => setActiveView('schedule')}>Schedule</button>
                  <button className={activeView === 'directions' ? 'active' : ''} onClick={() => setActiveView('directions')}>Directions</button>
                </div>
              </div>
              {activeView === 'schedule' ? (
                <Timeline segments={trip.segments} />
              ) : (
                <>
                <ol className="directions-list">
                  {trip.instructions.slice(0, showAllDirections ? undefined : 10).map((step, index) => (
                    <li key={`${step.instruction}-${index}`}>
                      <span>{String(index + 1).padStart(2, '0')}</span>
                      <div><strong>{step.instruction}</strong><small>{step.distance_miles} mi · {step.duration_minutes} min</small></div>
                    </li>
                  ))}
                </ol>
                {trip.instructions.length > 10 && (
                  <button className="show-directions" type="button" onClick={() => setShowAllDirections((value) => !value)}>
                    {showAllDirections ? 'Show fewer steps' : `Show all ${trip.instructions.length} steps`}
                  </button>
                )}
                </>
              )}
            </section>

            <section id="daily-logs" className="logs-section">
              <div className="section-heading">
                <div><div className="eyebrow">Record of duty status</div><h2>Daily logs</h2><p>{trip.logs.length} completed {trip.logs.length === 1 ? 'sheet' : 'sheets'} covering the full trip.</p></div>
                <button className="print-button" onClick={() => window.print()}>Print daily logs</button>
              </div>
              <div className="logs-grid">
                {trip.logs.map((log, index) => <EldLog key={log.date} log={log} index={index} />)}
              </div>
            </section>

          </div>
        )}
      </main>

      <footer>
        <span>RoadLedger · Planning aid, not a certified ELD</span>
        <span>Map data © OpenStreetMap contributors · CARTO · Routing by OSRM</span>
      </footer>
    </div>
  )
}
