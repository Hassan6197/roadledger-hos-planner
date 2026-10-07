import type { Segment } from '../types'

const labels: Record<string, string> = {
  driving: 'Driving',
  on_duty: 'On duty',
  off_duty: 'Off duty',
  sleeper: 'Sleeper berth',
}

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

export default function Timeline({ segments }: { segments: Segment[] }) {
  return (
    <ol className="timeline">
      {segments.map((segment, index) => (
        <li key={`${segment.start}-${segment.kind}-${index}`} className={`timeline__item timeline__item--${segment.status}`}>
          <div className="timeline__rail"><span /></div>
          <div className="timeline__content">
            <div className="timeline__meta">
              <span>{formatTime(segment.start)}</span>
              <span>{segment.duration_hours.toFixed(1)}h</span>
            </div>
            <h3>{segment.label}</h3>
            <p>{labels[segment.status]}{segment.miles ? ` · ${Math.round(segment.miles)} miles` : ''}</p>
          </div>
        </li>
      ))}
    </ol>
  )
}

