'use client'
import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { deviceApi, farmApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'

// Device status colours on the map
const STATUS_COLOR: Record<string, string> = {
  ONLINE: '#10b981', OFFLINE: '#475569', WARNING: '#facc15', ERROR: '#ef4444',
  MAINTENANCE: '#60a5fa', UNREGISTERED: '#6b7280',
}

const DEVICE_ICON: Record<string, string> = {
  WATCHTOWER: '📡', SOILNODE: '🌱', FEEDER: '🪣',
  WORKERTAG: '👷', FENCEGRID: '🔒', HUB: '🖥️', AQUASENSE: '🌊',
}

interface Device {
  id: string; name: string; type: string; status: string
  lat?: number; lng?: number; battery_pct?: number
}

interface Farm {
  id: string; name: string; lat?: number; lng?: number; boundary_geojson?: unknown
}

export default function FarmMap() {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstance = useRef<unknown>(null)
  const currentFarm = useStore((s) => s.currentFarm) as Farm | null

  const { data: devicesData } = useQuery<{ data: Device[] }>({
    queryKey: ['devices', currentFarm?.id],
    queryFn: () => deviceApi.list(currentFarm!.id),
    enabled: !!currentFarm,
    refetchInterval: 15_000,
  })

  const { data: farmData } = useQuery<{ data: Farm }>({
    queryKey: ['farm', currentFarm?.id],
    queryFn: () => farmApi.get(currentFarm!.id),
    enabled: !!currentFarm,
  })

  const devices = devicesData?.data || []
  const farm = farmData?.data

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return

    // Dynamically import Leaflet (SSR safe)
    import('leaflet').then(async (L) => {
      // @ts-ignore — Next.js handles CSS imports, but TS lacks the type declaration
      import('leaflet/dist/leaflet.css')

      const center: [number, number] = farm?.lat && farm?.lng
        ? [farm.lat, farm.lng]
        : [7.3775, 3.9470] // Default: Ibadan, Nigeria

      const map = L.map(mapRef.current!, {
        center,
        zoom: 15,
        zoomControl: true,
      })

      // Ensure Geoman is loaded
      // @ts-ignore
      await import('@geoman-io/leaflet-geoman-free')
      // @ts-ignore
      import('@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css')

      // @ts-ignore Add Geoman controls to the map
      map.pm.addControls({
        position: 'topleft',
        drawMarker: false,
        drawCircleMarker: false,
        drawPolyline: false,
        drawRectangle: true,
        drawCircle: false,
        editMode: true,
        dragMode: true,
        cutPolygon: false,
        removalMode: true,
      })

      // @ts-ignore Handle polygon creation
      map.on('pm:create', (e) => {
        const geojson = (e.layer as any).toGeoJSON()
        if (farm?.id) {
          farmApi.update(farm.id, { boundary_geojson: geojson })
            .catch(err => console.error('Failed to save boundary', err))
        }
      })

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map)

      mapInstance.current = { map, L, markers: [] as unknown[] }

      // Draw farm boundary if available
      if (farm?.boundary_geojson) {
        L.geoJSON(farm.boundary_geojson as Parameters<typeof L.geoJSON>[0], {
          style: {
            color: '#10b981', weight: 2, opacity: 0.8,
            fillColor: '#10b981', fillOpacity: 0.06,
          },
        }).addTo(map)
      }
    })

    return () => {
      if (mapInstance.current) {
        const { map } = mapInstance.current as { map: { remove: () => void } }
        map.remove()
        mapInstance.current = null
      }
    }
  }, [farm])

  // Update device markers
  useEffect(() => {
    if (!mapInstance.current) return
    const { map, L, markers } = mapInstance.current as {
      map: { addLayer: (l: unknown) => void },
      L: typeof import('leaflet'),
      markers: unknown[]
    }

    // Remove old markers
    markers.forEach((m: unknown) => (m as { remove: () => void }).remove())
    markers.length = 0

    devices.forEach(device => {
      if (!device.lat || !device.lng) return
      const color = STATUS_COLOR[device.status] || STATUS_COLOR.OFFLINE
      const emoji = DEVICE_ICON[device.type] || '📍'

      const icon = L.divIcon({
        html: `
          <div style="
            background: ${color}22;
            border: 2px solid ${color};
            border-radius: 50%;
            width: 36px; height: 36px;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px;
            box-shadow: 0 0 12px ${color}44;
          ">${emoji}</div>`,
        className: '',
        iconSize: [36, 36],
        iconAnchor: [18, 18],
      })

      const marker = L.marker([device.lat, device.lng], { icon })
        .addTo(map as Parameters<typeof L.marker>[1] extends object ? unknown : never)
        .bindPopup(`
          <div style="font-family: monospace; font-size: 12px; min-width: 160px;">
            <strong style="font-family: sans-serif; font-size: 14px;">${device.name}</strong><br>
            <span style="color: ${color}">● ${device.status}</span><br>
            Type: ${device.type}<br>
            ${device.battery_pct != null ? `Battery: ${Math.round(device.battery_pct)}%` : ''}
          </div>
        `)

      markers.push(marker)
    })
  }, [devices])

  if (!currentFarm) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 font-mono text-sm">
        Select a farm to view the map
      </div>
    )
  }

  return (
    <div className="relative w-full h-full">
      <div ref={mapRef} className="w-full h-full rounded-xl overflow-hidden" />
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-[#0f1117]/90 backdrop-blur border border-white/10 rounded-xl p-3 space-y-1.5 z-[1000]">
        {Object.entries(STATUS_COLOR).filter(([k]) => k !== 'UNREGISTERED').map(([status, color]) => (
          <div key={status} className="flex items-center gap-2 text-xs font-mono text-slate-300">
            <span style={{ background: color, borderRadius: '50%', width: 8, height: 8, display: 'inline-block' }} />
            {status}
          </div>
        ))}
      </div>
    </div>
  )
}
