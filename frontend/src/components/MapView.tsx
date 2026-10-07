import { useEffect, useRef } from 'react'
import {
  AttributionControl,
  LngLatBounds,
  Map,
  Marker,
  NavigationControl,
  Popup,
  setWorkerUrl,
  type GeoJSONSource,
  type Map as MapInstance,
} from 'maplibre-gl'
import workerSource from 'maplibre-gl/dist/maplibre-gl-worker.mjs?raw'
import type { TripPlan } from '../types'

const workerUrl = URL.createObjectURL(new Blob([workerSource], { type: 'text/javascript' }))
setWorkerUrl(workerUrl)

const colors: Record<string, string> = {
  origin: '#14201f',
  pickup: '#1d6b5c',
  dropoff: '#f26a36',
  fuel: '#d89a25',
  break: '#3876a8',
  sleeper: '#725aa8',
  restart: '#725aa8',
}

const markerLabels: Record<string, string> = {
  origin: 'S',
  pickup: 'P',
  dropoff: 'D',
  fuel: 'F',
  break: 'B',
  sleeper: 'R',
  restart: 'R',
}

export default function MapView({ trip, loading = false }: { trip?: TripPlan; loading?: boolean }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapInstance | null>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = new Map({
      container: containerRef.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [-98.5, 39.5],
      zoom: 3,
      attributionControl: false,
    })
    map.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    map.addControl(new AttributionControl({ compact: true, customAttribution: 'CARTO' }))
    const observer = new ResizeObserver(() => map.resize())
    observer.observe(containerRef.current)
    requestAnimationFrame(() => map.resize())
    mapRef.current = map
    return () => {
      observer.disconnect()
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !trip) return
    const renderTrip = () => {
      map.resize()
      const existing = map.getSource('route') as GeoJSONSource | undefined
      const data = {
        type: 'Feature',
        properties: {},
        geometry: { type: 'LineString', coordinates: trip.coordinates },
      } as const
      if (existing) existing.setData(data)
      else {
        map.addSource('route', { type: 'geojson', data })
        map.addLayer({
          id: 'route-shadow',
          type: 'line',
          source: 'route',
          paint: { 'line-color': '#ffffff', 'line-width': 8, 'line-opacity': 0.82 },
        })
        map.addLayer({
          id: 'route-line',
          type: 'line',
          source: 'route',
          paint: { 'line-color': '#f26a36', 'line-width': 4 },
        })
      }
      document.querySelectorAll('.route-marker').forEach((node) => node.remove())
      trip.stops.forEach((stop) => {
        const element = document.createElement('button')
        element.className = `route-marker route-marker--${stop.type}`
        element.type = 'button'
        element.style.background = colors[stop.type] || '#14201f'
        element.setAttribute('aria-label', stop.label)
        const label = document.createElement('span')
        label.textContent = markerLabels[stop.type] || '•'
        element.appendChild(label)
        new Marker({ element })
          .setLngLat(stop.coordinate)
          .setPopup(new Popup({ offset: 18 }).setHTML(`<strong>${stop.label}</strong><br><span>${new Date(stop.at).toLocaleString()}</span>`))
          .addTo(map)
      })
      const bounds = trip.coordinates.reduce(
        (box, coordinate) => box.extend(coordinate),
        new LngLatBounds(trip.coordinates[0], trip.coordinates[0]),
      )
      map.fitBounds(bounds, { padding: 58, maxZoom: 8, duration: 900 })
    }
    if (map.loaded()) renderTrip()
    else map.once('load', renderTrip)
  }, [trip])

  return (
    <div className="map-shell">
      <div ref={containerRef} className="map" aria-label="Trip route map" />
      {!trip && (
        <div className="map-empty">
          <span className="map-empty__line" />
          <strong>Route workspace</strong>
          <p>Enter your stops to map the route and calculate every HOS event.</p>
        </div>
      )}
      {loading && (
        <div className="map-loading" role="status" aria-live="polite">
          <div><span className="spinner" /><strong>Building your plan</strong></div>
          <p>Finding locations, routing the miles, and checking HOS limits.</p>
          <i><b /></i>
        </div>
      )}
      {trip && !loading && (
        <div className="map-legend" aria-label="Map legend">
          <span><i className="legend-start">S</i> Start</span>
          <span><i className="legend-pickup">P</i> Pickup</span>
          <span><i className="legend-break">B</i> Break</span>
          <span><i className="legend-rest">R</i> Rest</span>
          <span><i className="legend-finish">D</i> Drop-off</span>
        </div>
      )}
    </div>
  )
}
