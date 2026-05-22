'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { deviceApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Radio, Battery, Clock, AlertTriangle, CheckCircle, WifiOff, Wrench } from 'lucide-react'
import RegisterDeviceModal from '@/components/devices/RegisterDeviceModal'
import { useRouter } from 'next/navigation'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'

interface Device {
  id: string; name: string; type: string; serial?: string
  status: string; battery_pct?: number; firmware_ver?: string
  last_seen_at?: string; lat?: number; lng?: number
}

const STATUS_CONFIG: Record<string, { icon: React.ElementType; color: string; dot: string; label: string }> = {
  ONLINE:      { icon: CheckCircle,  color: 'text-brand',      dot: 'bg-brand',        label: 'Online' },
  OFFLINE:     { icon: WifiOff,      color: 'text-slate-500',  dot: 'bg-slate-600',    label: 'Offline' },
  WARNING:     { icon: AlertTriangle,color: 'text-yellow-400', dot: 'bg-yellow-400',   label: 'Warning' },
  ERROR:       { icon: AlertTriangle,color: 'text-red-400',    dot: 'bg-red-400',      label: 'Error' },
  MAINTENANCE: { icon: Wrench,       color: 'text-blue-400',   dot: 'bg-blue-400',     label: 'Maintenance' },
}

const TYPE_LABELS: Record<string, string> = {
  WATCHTOWER: 'Watchtower', SOILNODE: 'Soil Sensor', FEEDER: 'Feeder',
  WORKERTAG: 'Worker Tag', FENCEGRID: 'Fencegrid', HUB: 'Hub', AQUASENSE: 'Aquasense',
}

function BatteryBar({ pct }: { pct: number }) {
  const color = pct < 20 ? 'bg-red-400' : pct < 40 ? 'bg-yellow-400' : 'bg-brand'
  return (
    <div className="flex items-center gap-2">
      <Battery className={clsx('w-3.5 h-3.5 shrink-0', pct < 20 ? 'text-red-400' : 'text-slate-500')} />
      <div className="flex-1 bg-white/5 rounded-full h-1.5">
        <div className={clsx('h-full rounded-full transition-all', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 font-mono">{Math.round(pct)}%</span>
    </div>
  )
}

function DeviceCard({ device, farmId }: { device: Device; farmId: string }) {
  const router = useRouter()
  const cfg = STATUS_CONFIG[device.status] || STATUS_CONFIG.OFFLINE
  const StatusIcon = cfg.icon

  return (
    <div onClick={() => router.push(`/devices/${device.id}`)}
      className="card group cursor-pointer hover:border-brand/20 hover:bg-white/[0.04] transition-all">
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className={clsx('w-1.5 h-1.5 rounded-full shrink-0', cfg.dot)} />
            <span className="text-xs font-mono text-slate-500 uppercase tracking-wider truncate">
              {TYPE_LABELS[device.type] || device.type}
            </span>
          </div>
          <h3 className="text-sm font-semibold text-white group-hover:text-brand transition-colors truncate">
            {device.name}
          </h3>
          {device.serial && <p className="text-xs text-slate-600 font-mono mt-0.5">{device.serial}</p>}
        </div>
        <StatusIcon className={clsx('w-4 h-4 shrink-0 ml-2', cfg.color)} />
      </div>

      <div className="space-y-1.5 mt-3 pt-3 border-t border-white/5">
        {device.battery_pct != null && <BatteryBar pct={device.battery_pct} />}
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
  const [showModal, setShowModal] = useState(false)

  const { data, isLoading } = useQuery<{ data: Device[] }>({
    queryKey: ['devices', currentFarm?.id],
    queryFn: () => deviceApi.list(currentFarm!.id),
    enabled: !!currentFarm,
    refetchInterval: 15_000,
  })

  const devices = data?.data || []
  const online = devices.filter(d => d.status === 'ONLINE').length
  const warning = devices.filter(d => d.status === 'WARNING').length
  const offline = devices.filter(d => d.status === 'OFFLINE' || d.status === 'ERROR').length

  return (
    <>
      {showModal && <RegisterDeviceModal onClose={() => setShowModal(false)} />}

      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-white">Devices</h1>
            <p className="text-sm text-slate-400 mt-0.5">
              {online} online{warning > 0 ? ` · ${warning} warning` : ''} · {offline} offline
            </p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Radio className="w-4 h-4" /> Register Device
          </button>
        </div>

        {/* Status summary */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Online', count: online, color: 'text-brand', bg: 'bg-brand/10 border-brand/15' },
            { label: 'Warning', count: warning, color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/15' },
            { label: 'Offline', count: offline, color: 'text-slate-400', bg: 'bg-white/5 border-white/8' },
          ].map(({ label, count, color, bg }) => (
            <div key={label} className={clsx('rounded-xl px-4 py-3 text-center border', bg)}>
              <p className={clsx('text-2xl font-display font-bold', color)}>{count}</p>
              <p className="text-xs text-slate-400 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {isLoading ? (
          <div className="text-slate-500 font-mono text-sm animate-pulse">Loading devices...</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {devices.map(d => <DeviceCard key={d.id} device={d} farmId={currentFarm!.id} />)}
            {devices.length === 0 && (
              <div className="col-span-full text-center text-slate-500 py-16">
                <Radio className="w-10 h-10 mx-auto mb-3 opacity-20" />
                <p>No devices registered.</p>
                <button onClick={() => setShowModal(true)}
                  className="mt-3 text-brand text-sm hover:underline">Register your first device →</button>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}
