'use client'
import { useQuery } from '@tanstack/react-query'
import { deviceApi, maintenanceApi, alertApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { useParams, useRouter } from 'next/navigation'
import TelemetryChart from '@/components/devices/TelemetryChart'
import { ArrowLeft, Radio, Battery, Clock, Wifi, WifiOff, AlertTriangle, CheckCircle, Wrench } from 'lucide-react'
import clsx from 'clsx'
import { formatDistanceToNow, format } from 'date-fns'

const STATUS_CFG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  ONLINE:      { icon: CheckCircle, color: 'text-brand', label: 'Online' },
  OFFLINE:     { icon: WifiOff, color: 'text-slate-500', label: 'Offline' },
  WARNING:     { icon: AlertTriangle, color: 'text-yellow-400', label: 'Warning' },
  ERROR:       { icon: AlertTriangle, color: 'text-red-400', label: 'Error' },
  MAINTENANCE: { icon: Wrench, color: 'text-blue-400', label: 'Maintenance' },
}

export default function DeviceDetailPage() {
  const params = useParams()
  const router = useRouter()
  const currentFarm = useStore(s => s.currentFarm)
  const deviceId = params.deviceId as string

  const { data: devData, isLoading } = useQuery({
    queryKey: ['device', currentFarm?.id, deviceId],
    queryFn: () => deviceApi.get(currentFarm!.id, deviceId),
    enabled: !!currentFarm,
    refetchInterval: 15_000,
  })

  const { data: alertsData } = useQuery({
    queryKey: ['device-alerts', currentFarm?.id, deviceId],
    queryFn: () => alertApi.list(currentFarm!.id, { status: 'OPEN' }),
    enabled: !!currentFarm,
  })

  const { data: maintData } = useQuery({
    queryKey: ['device-maint', currentFarm?.id, deviceId],
    queryFn: () => maintenanceApi.forDevice(currentFarm!.id, deviceId),
    enabled: !!currentFarm,
  })

  const device = devData?.data
  const deviceAlerts = ((alertsData?.data || []) as Array<{ device_id?: string; severity: string; title: string; created_at: string }>).filter(
    (a) => a.device_id === deviceId
  )
  const maintenance = (maintData?.data || []) as Array<{ id: string; type: string; description: string; performed_at: string }>

  if (isLoading) {
    return <div className="p-6 text-slate-500 font-mono text-sm animate-pulse">Loading device...</div>
  }
  if (!device) {
    return <div className="p-6 text-slate-500">Device not found.</div>
  }

  const cfg = STATUS_CFG[device.status] || STATUS_CFG.OFFLINE
  const StatusIcon = cfg.icon

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Back */}
      <button onClick={() => router.back()}
        className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Devices
      </button>

      {/* Device header */}
      <div className="card">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">{device.type}</span>
            <h1 className="text-xl font-display font-bold text-white mt-0.5">{device.name}</h1>
            {device.serial && <p className="text-xs text-slate-600 font-mono mt-1">{device.serial}</p>}
          </div>
          <div className={clsx('flex items-center gap-1.5 text-sm font-mono', cfg.color)}>
            <StatusIcon className="w-4 h-4" />
            {cfg.label}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 pt-5 border-t border-white/5">
          {device.battery_pct != null && (
            <div>
              <p className="text-xs text-slate-500 font-mono mb-1 flex items-center gap-1">
                <Battery className="w-3 h-3" /> Battery
              </p>
              <p className={clsx('text-sm font-semibold', device.battery_pct < 20 ? 'text-red-400' : device.battery_pct < 40 ? 'text-yellow-400' : 'text-white')}>
                {Math.round(device.battery_pct)}%
              </p>
            </div>
          )}
          {device.firmware_ver && (
            <div>
              <p className="text-xs text-slate-500 font-mono mb-1">Firmware</p>
              <p className="text-sm text-white font-mono">{device.firmware_ver}</p>
            </div>
          )}
          {device.last_seen_at && (
            <div>
              <p className="text-xs text-slate-500 font-mono mb-1 flex items-center gap-1">
                <Clock className="w-3 h-3" /> Last Seen
              </p>
              <p className="text-sm text-white">{formatDistanceToNow(new Date(device.last_seen_at), { addSuffix: true })}</p>
            </div>
          )}
          {device.lat && device.lng && (
            <div>
              <p className="text-xs text-slate-500 font-mono mb-1">Coordinates</p>
              <p className="text-sm text-white font-mono">{device.lat.toFixed(4)}, {device.lng.toFixed(4)}</p>
            </div>
          )}
        </div>
      </div>

      {/* Telemetry charts */}
      <div>
        <h2 className="text-sm font-semibold text-white mb-3">Sensor Readings</h2>
        <TelemetryChart farmId={currentFarm!.id} deviceId={deviceId} />
      </div>

      {/* Active alerts on this device */}
      {deviceAlerts.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-white mb-3">Active Alerts</h2>
          <div className="space-y-2">
            {deviceAlerts.map((a, i) => (
              <div key={i} className="card flex items-start gap-3">
                <AlertTriangle className={clsx('w-4 h-4 shrink-0 mt-0.5',
                  a.severity === 'CRITICAL' ? 'text-red-400' : a.severity === 'HIGH' ? 'text-orange-400' : 'text-yellow-400'
                )} />
                <div>
                  <p className="text-sm text-white">{a.title}</p>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">
                    {formatDistanceToNow(new Date(a.created_at), { addSuffix: true })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Maintenance history */}
      {maintenance.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-white mb-3">Maintenance History</h2>
          <div className="space-y-2">
            {maintenance.slice(0, 5).map(m => (
              <div key={m.id} className="card flex items-start gap-3">
                <Wrench className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-white">{m.description}</p>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">
                    {m.type} · {format(new Date(m.performed_at), 'dd MMM yyyy')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
