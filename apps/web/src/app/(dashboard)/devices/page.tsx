'use client'
import { useQuery } from '@tanstack/react-query'
import { deviceApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Radio, Battery, Clock, AlertTriangle, CheckCircle, WifiOff, Wrench } from 'lucide-react'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'

interface Device {
  id: string; name: string; type: string; serial?: string
  status: string; battery_pct?: number; firmware_ver?: string
  last_seen_at?: string; lat?: number; lng?: number; sector_id?: string
}

const STATUS_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  ONLINE:      { icon: CheckCircle,  color: 'text-brand',   label: 'Online' },
  OFFLINE:     { icon: WifiOff,      color: 'text-slate-500', label: 'Offline' },
  WARNING:     { icon: AlertTriangle,color: 'text-yellow-400', label: 'Warning' },
  ERROR:       { icon: AlertTriangle,color: 'text-red-400',  label: 'Error' },
  MAINTENANCE: { icon: Wrench,       color: 'text-blue-400', label: 'Maintenance' },
}

const TYPE_LABELS: Record<string, string> = {
  WATCHTOWER: 'Watchtower', SOILNODE: 'Soil Sensor', FEEDER: 'Feeder',
  WORKERTAG: 'Worker Tag', FENCEGRID: 'Fencegrid', HUB: 'Hub', AQUASENSE: 'Aquasense',
}

function BatteryBar({ pct }: { pct: number }) {
  const color = pct < 20 ? 'bg-red-400' : pct < 40 ? 'bg-yellow-400' : 'bg-brand'
  return (
    <div className="flex items-center gap-2">
      <Battery className={clsx('w-3.5 h-3.5', pct < 20 ? 'text-red-400' : 'text-slate-400')} />
      <div className="flex-1 bg-white/5 rounded-full h-1.5 max-w-[80px]">
        <div className={clsx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 font-mono">{Math.round(pct)}%</span>
    </div>
  )
}

function DeviceCard({ device }: { device: Device }) {
  const cfg = STATUS_CONFIG[device.status] || STATUS_CONFIG.OFFLINE
  const StatusIcon = cfg.icon

  return (
    <div className="card group cursor-pointer hover:border-brand/20 transition-all">
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">
            {TYPE_LABELS[device.type] || device.type}
          </span>
          <h3 className="text-sm font-semibold text-white group-hover:text-brand transition-colors mt-0.5">
            {device.name}
          </h3>
          {device.serial && (
            <p className="text-xs text-slate-600 font-mono">{device.serial}</p>
          )}
        </div>
        <div className={clsx('flex items-center gap-1 text-xs font-mono', cfg.color)}>
          <StatusIcon className="w-3.5 h-3.5" />
          {cfg.label}
        </div>
      </div>

      <div className="space-y-2">
        {device.battery_pct !== null && device.battery_pct !== undefined && (
          <BatteryBar pct={device.battery_pct} />
        )}
        {device.last_seen_at && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Clock className="w-3 h-3" />
            {formatDistanceToNow(new Date(device.last_seen_at), { addSuffix: true })}
          </div>
        )}
        {device.firmware_ver && (
          <div className="text-xs text-slate-600 font-mono">fw {device.firmware_ver}</div>
        )}
      </div>
    </div>
  )
}

export default function DevicesPage() {
  const currentFarm = useStore((s) => s.currentFarm)

  const { data, isLoading } = useQuery<{ data: Device[] }>({
    queryKey: ['devices', currentFarm?.id],
    queryFn: () => deviceApi.list(currentFarm!.id),
    enabled: !!currentFarm,
    refetchInterval: 15_000,
  })

  const devices = data?.data || []
  const online = devices.filter(d => d.status === 'ONLINE').length
  const warning = devices.filter(d => d.status === 'WARNING').length
  const offline = devices.filter(d => d.status === 'OFFLINE').length

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">Devices</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {online} online · {warning > 0 ? `${warning} warning · ` : ''}{offline} offline
          </p>
        </div>
        <button className="btn-primary flex items-center gap-2 text-sm">
          <Radio className="w-4 h-4" /> Register Device
        </button>
      </div>

      {/* Status summary bar */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Online', count: online, color: 'text-brand', bg: 'bg-brand/10' },
          { label: 'Warning', count: warning, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
          { label: 'Offline', count: offline, color: 'text-slate-400', bg: 'bg-white/5' },
        ].map(({ label, count, color, bg }) => (
          <div key={label} className={clsx('rounded-xl px-4 py-3 text-center', bg)}>
            <p className={clsx('text-2xl font-display font-bold', color)}>{count}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {isLoading ? (
        <div className="text-slate-500 font-mono text-sm">Loading devices...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {devices.map(d => <DeviceCard key={d.id} device={d} />)}
          {devices.length === 0 && (
            <div className="col-span-full text-center text-slate-500 py-16">
              <Radio className="w-10 h-10 mx-auto mb-3 opacity-20" />
              <p>No devices registered yet.</p>
              <p className="text-sm mt-1">Click "Register Device" to add your first device.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
