'use client'
import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { deviceApi, farmApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Layers, PenTool, Trash2, Edit2 } from 'lucide-react'

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
  const tileLayerRef = useRef<unknown>(null)
  const [mapStyle, setMapStyle] = useState<'satellite' | 'dark'>('satellite')
  const [isDrawing, setIsDrawing] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  
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

      // @ts-ignore Set global Geoman options
      map.pm.setGlobalOptions({ 
        pathOptions: { 
          color: '#0ea5e9', weight: 3, opacity: 0.8,
          fillColor: '#0ea5e9', fillOpacity: 0.1 
        } 
      })

      // @ts-ignore Handle polygon creation and editing
      const saveBoundary = (layer: any) => {
        const geojson = layer.toGeoJSON()
        if (farm?.id) {
          farmApi.update(farm.id, { boundary_geojson: geojson })
            .catch(err => console.error('Failed to save boundary', err))
        }
      }

      // @ts-ignore
      map.on('pm:create', (e) => saveBoundary(e.layer))
      // @ts-ignore
      map.on('pm:remove', () => farmApi.update(farm!.id, { boundary_geojson: null }))

      const tileLayer = L.tileLayer(
        mapStyle === 'satellite'
          ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
          : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', 
        {
          attribution: '© Esri / CartoDB',
          maxZoom: 19,
        }
      ).addTo(map)
      
      tileLayerRef.current = tileLayer

      mapInstance.current = { map, L, markers: [] as unknown[] }

      if (farm?.boundary_geojson) {
        // @ts-ignore
        const layer = L.geoJSON(farm.boundary_geojson, {
          style: {
            color: '#0ea5e9', weight: 3, opacity: 0.9,
            fillColor: '#0ea5e9', fillOpacity: 0.1,
            dashArray: '8, 8'
          },
        }).addTo(map)
        
        // @ts-ignore Allow editing of existing boundary
        layer.on('pm:edit', () => saveBoundary(layer))
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

  // Handle map style changes
  useEffect(() => {
    if (tileLayerRef.current) {
      const url = mapStyle === 'satellite'
        ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      ;(tileLayerRef.current as any).setUrl(url)
    }
  }, [mapStyle])

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
          <div class="relative flex h-10 w-10">
            ${device.status === 'ONLINE' ? `<span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style="background: ${color};"></span>` : ''}
            <span class="relative inline-flex h-10 w-10 items-center justify-center rounded-full border-2 bg-[#0f1117] shadow-lg" style="border-color: ${color}; box-shadow: 0 0 12px ${color}88;">
              <span class="text-lg">${emoji}</span>
            </span>
          </div>`,
        className: 'bg-transparent border-0',
        iconSize: [40, 40],
        iconAnchor: [20, 20],
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
    <div className="relative w-full h-full group">
      <div ref={mapRef} className="w-full h-full rounded-xl overflow-hidden shadow-2xl border border-white/5" />
      
      {/* Top Right Custom Toolbar */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
        <div className="bg-[#0f1117]/80 backdrop-blur-md border border-white/10 rounded-xl p-1.5 flex flex-col gap-1 shadow-xl">
          <button 
            onClick={() => setMapStyle(s => s === 'satellite' ? 'dark' : 'satellite')}
            className="p-2.5 rounded-lg hover:bg-white/10 text-slate-300 transition-colors tooltip-left"
            title="Toggle Map Style"
          >
            <Layers className="w-5 h-5" />
          </button>
          <div className="h-px bg-white/10 w-full my-1" />
          <button 
            onClick={() => {
              const map = (mapInstance.current as any)?.map
              if (map) {
                if (isDrawing) map.pm.disableDraw()
                else map.pm.enableDraw('Polygon')
                setIsDrawing(!isDrawing)
                setIsEditing(false)
              }
            }}
            className={`p-2.5 rounded-lg transition-colors ${isDrawing ? 'bg-primary text-white' : 'hover:bg-white/10 text-slate-300'}`}
            title="Draw Perimeter"
          >
            <PenTool className="w-5 h-5" />
          </button>
          <button 
            onClick={() => {
              const map = (mapInstance.current as any)?.map
              if (map) {
                map.pm.toggleGlobalEditMode()
                setIsEditing(!isEditing)
                setIsDrawing(false)
              }
            }}
            className={`p-2.5 rounded-lg transition-colors ${isEditing ? 'bg-primary text-white' : 'hover:bg-white/10 text-slate-300'}`}
            title="Edit Boundaries"
          >
            <Edit2 className="w-5 h-5" />
          </button>
          <button 
            onClick={() => {
              const map = (mapInstance.current as any)?.map
              if (map) map.pm.toggleGlobalRemovalMode()
            }}
            className="p-2.5 rounded-lg hover:bg-red-500/20 text-slate-300 hover:text-red-400 transition-colors"
            title="Delete Boundary"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-[#0f1117]/80 backdrop-blur-md border border-white/10 rounded-xl p-3 space-y-2 z-[1000] shadow-xl">
        <div className="text-xs font-semibold text-slate-400 mb-1 tracking-wider uppercase">Live Status</div>
        {Object.entries(STATUS_COLOR).filter(([k]) => k !== 'UNREGISTERED').map(([status, color]) => (
          <div key={status} className="flex items-center gap-2 text-xs font-mono text-slate-200">
            <span style={{ background: color, borderRadius: '50%', width: 8, height: 8, display: 'inline-block', boxShadow: `0 0 8px ${color}` }} />
            {status}
          </div>
        ))}
      </div>
    </div>
  )
}
