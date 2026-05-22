'use client'
import { useQuery } from '@tanstack/react-query'
import { farmApi, alertApi, deviceApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { BarChart3, TrendingDown, Activity, Clock } from 'lucide-react'
import { format, subDays } from 'date-fns'

export default function ReportsPage() {
  const currentFarm = useStore((s) => s.currentFarm)

  const { data: summaryData } = useQuery({
    queryKey: ['farm-summary', currentFarm?.id],
    queryFn: () => farmApi.summary(currentFarm!.id),
    enabled: !!currentFarm,
  })

  const { data: alertsData } = useQuery({
    queryKey: ['alerts-report', currentFarm?.id],
    queryFn: () => alertApi.list(currentFarm!.id, { limit: 200 }),
    enabled: !!currentFarm,
  })

  const { data: devicesData } = useQuery({
    queryKey: ['devices', currentFarm?.id],
    queryFn: () => deviceApi.list(currentFarm!.id),
    enabled: !!currentFarm,
  })

  const summary = (summaryData as { data: Record<string, number & { farm?: unknown }> } | undefined)?.data
  const alerts = ((alertsData as { data: unknown[] } | undefined)?.data || []) as Array<{ severity: string; status: string; created_at: string }>
  const devices = ((devicesData as { data: unknown[] } | undefined)?.data || []) as Array<{ status: string; battery_pct?: number; name: string }>

  const alertsBySeverity = {
    CRITICAL: alerts.filter(a => a.severity === 'CRITICAL').length,
    HIGH: alerts.filter(a => a.severity === 'HIGH').length,
    MEDIUM: alerts.filter(a => a.severity === 'MEDIUM').length,
    LOW: alerts.filter(a => a.severity === 'LOW').length,
  }

  const lowBattery = devices.filter(d => d.battery_pct != null && d.battery_pct < 30)
  const onlineRate = devices.length > 0
    ? Math.round((devices.filter(d => d.status === 'ONLINE').length / devices.length) * 100)
    : 0

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-white">Reports</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Daily summary · {format(new Date(), 'dd MMM yyyy')}
        </p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Device Uptime', value: `${onlineRate}%`, icon: Activity, color: 'text-brand' },
          { label: 'Open Alerts', value: String(summary?.open_alerts ?? 0), icon: BarChart3, color: 'text-orange-400' },
          { label: 'Total Devices', value: String(summary?.device_count ?? 0), icon: Activity, color: 'text-slate-300' },
          { label: 'Low Battery', value: String(lowBattery.length), icon: TrendingDown, color: 'text-yellow-400' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card">
            <Icon className={`w-5 h-5 ${color} mb-2`} />
            <p className={`text-2xl font-display font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Alert breakdown */}
      <div className="card">
        <h2 className="text-sm font-semibold text-white mb-4">Alert Breakdown</h2>
        <div className="space-y-3">
          {Object.entries(alertsBySeverity).map(([sev, count]) => {
            const pct = alerts.length > 0 ? (count / alerts.length) * 100 : 0
            const color = sev === 'CRITICAL' ? 'bg-red-400' : sev === 'HIGH' ? 'bg-orange-400' : sev === 'MEDIUM' ? 'bg-yellow-400' : 'bg-slate-400'
            return (
              <div key={sev} className="flex items-center gap-3">
                <span className="w-16 text-xs font-mono text-slate-400">{sev}</span>
                <div className="flex-1 bg-white/5 rounded-full h-2">
                  <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                </div>
                <span className="w-8 text-xs font-mono text-slate-300 text-right">{count}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Low battery devices */}
      {lowBattery.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-3">Devices Needing Attention</h2>
          <div className="space-y-2">
            {lowBattery.map((d, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-slate-300">{d.name}</span>
                <span className="font-mono text-yellow-400">{Math.round(d.battery_pct!)}% battery</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
