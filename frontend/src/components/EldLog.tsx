import logSheet from '../assets/log-sheet.png'
import type { DailyLog, DutyStatus } from '../types'

const yByStatus: Record<DutyStatus, number> = {
  off_duty: 190,
  sleeper: 211,
  driving: 232,
  on_duty: 252,
}

function pathFor(entries: DailyLog['entries']) {
  const x = (hour: number) => 65 + (hour / 24) * 389
  if (!entries.length) return ''
  let path = `M ${x(entries[0].start_hour)} ${yByStatus[entries[0].status]}`
  entries.forEach((entry, index) => {
    const y = yByStatus[entry.status]
    path += ` L ${x(entry.end_hour)} ${y}`
    const next = entries[index + 1]
    if (next) path += ` L ${x(entry.end_hour)} ${yByStatus[next.status]}`
  })
  return path
}

const shortName = (value: string) => value.split(',').slice(0, 2).join(',').slice(0, 32)

export default function EldLog({ log, index }: { log: DailyLog; index: number }) {
  const total = (status: DutyStatus) => (log.totals[status] || 0).toFixed(2).replace('.00', '')
  return (
    <article className="log-card" aria-label={`Daily log for ${log.date}`}>
      <div className="log-card__heading">
        <div>
          <span>Log {index + 1}</span>
          <h3>{new Date(`${log.date}T12:00:00`).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</h3>
        </div>
        <div className="log-card__miles">{log.total_miles.toLocaleString()} mi</div>
      </div>
      <div className="paper-log">
        <img src={logSheet} alt="Driver's daily log form" />
        <svg viewBox="0 0 513 518" role="img" aria-label="Completed graph grid and log fields">
          <text x="225" y="34" textAnchor="middle" className="log-ink log-small">{log.date}</text>
          <text x="72" y="57" className="log-ink log-small">{shortName(log.from)}</text>
          <text x="302" y="57" className="log-ink log-small">{shortName(log.to)}</text>
          <text x="102" y="96" textAnchor="middle" className="log-ink">{log.total_miles}</text>
          <text x="337" y="91" textAnchor="middle" className="log-ink log-small">RoadLedger Demo Carrier</text>
          <path d={pathFor(log.entries)} className="duty-line" />
          <text x="477" y="192" className="log-ink log-total">{total('off_duty')}</text>
          <text x="477" y="213" className="log-ink log-total">{total('sleeper')}</text>
          <text x="477" y="234" className="log-ink log-total">{total('driving')}</text>
          <text x="477" y="255" className="log-ink log-total">{total('on_duty')}</text>
          {log.remarks.map((remark, remarkIndex) => (
            <text key={remark} x="26" y={296 + remarkIndex * 15} className="log-ink log-remark">{remark.slice(0, 72)}</text>
          ))}
          <text x="125" y="466" textAnchor="middle" className="log-ink log-small">{log.on_duty_today.toFixed(1)}</text>
          <text x="181" y="466" textAnchor="middle" className="log-ink log-small">{log.cycle_before.toFixed(1)}</text>
          <text x="237" y="466" textAnchor="middle" className="log-ink log-small">{log.cycle_after.toFixed(1)}</text>
        </svg>
      </div>
    </article>
  )
}

