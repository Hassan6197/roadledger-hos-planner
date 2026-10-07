export type DutyStatus = 'off_duty' | 'sleeper' | 'driving' | 'on_duty'

export interface Place {
  query: string
  name: string
  lat: number
  lon: number
}

export interface Stop {
  type: string
  label: string
  at: string
  coordinate: [number, number]
}

export interface Segment {
  start: string
  end: string
  status: DutyStatus
  label: string
  location: string
  duration_hours: number
  miles: number
  coordinate: [number, number]
  kind: string
}

export interface LogEntry {
  start_hour: number
  end_hour: number
  status: DutyStatus
  label: string
  location?: string
}

export interface DailyLog {
  date: string
  from: string
  to: string
  total_miles: number
  entries: LogEntry[]
  totals: Record<DutyStatus, number>
  remarks: string[]
  cycle_before: number
  on_duty_today: number
  cycle_after: number
}

export interface TripPlan {
  places: Place[]
  distance_miles: number
  drive_hours: number
  coordinates: [number, number][]
  instructions: { instruction: string; distance_miles: number; duration_minutes: number; leg: number }[]
  departure_at: string
  segments: Segment[]
  stops: Stop[]
  cycle: { initial_used: number; final_used: number; remaining: number }
  elapsed_hours: number
  arrival_at: string
  logs: DailyLog[]
}

export interface PlanResponse {
  trip: TripPlan
  assumptions: string[]
  attribution: string
}

