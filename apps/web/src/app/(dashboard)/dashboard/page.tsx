'use client'
import { useQuery } from '@tanstack/react-query'
import { farmApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Radio, Bell, AlertTriangle, Users, Wifi, Activity } from 'lucide-react'
import clsx from 'clsx'

interface Summary {
  farm: { id: string; name: string; timezone: string }
  device_count: number
  online_devices: number
  open_alerts: number
  critical_alerts: number
  workers_on_site: number
  last_updated: string
}

function StatCard({ label, value, sub, icon: Icon, accent }: {
  label: string; value: number | string; sub?: string; icon: React.ElementType; accent?: string
}) {
  return (
    <div className="card flex items-start gap-4">
      <div className={clsx('p-2.5 rounded-lg', accent || 'bg-brand/10')}>
        <Icon className={clsx('w-5 h-5', accent ? 'text-current' : 'text-brand')} />
      </div>
      <div>
        <p className="text-2xl font-display font-bold text-white">{value}</p>
        <p className="text-sm text-slate-400">{label}</p>
        {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const currentFarm = useStore((s) => s.currentFarm)

  const { data, isLoading } = useQuery<{ data: Summary }>({
    queryKey: ['farm-summary', currentFarm?.id],
    queryFn: () => farmApi.summary(currentFarm!.id),
    enabled: !!currentFarm,
    refetchInterval: 30_000,
  })

  const summary = data?.data

  if (!currentFarm) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-400">
        <Activity className="w-12 h-12 opacity-20" />
        <p>No farm selected. Create or select a farm to get started.</p>
      </div>
    )
  }

  if (isLoading) {
    return <div className="p-8 text-slate-500 font-mono text-sm">Loading farm data...</div>
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">{summary?.farm.name}</h1>
          <p className="text-sm text-slate-400 mt-0.5 font-mono">
            Last updated: {summary ? new Date(summary.last_updated).toLocaleTimeString() : '—'}
          </p>
        </div>
        <span className={clsx(
          'flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-full border',
          summary?.critical_alerts ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-brand/10 text-brand border-brand/20'
        )}>
          {summary?.critical_alerts ? <AlertTriangle className="w-3.5 h-3.5" /> : <Wifi className="w-3.5 h-3.5" />}
          {summary?.critical_alerts ? `${summary.critical_alerts} Critical` : 'All Clear'}
        </span>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Devices Online"
          value={`${summary?.online_devices ?? 0} / ${summary?.device_count ?? 0}`}
          icon={Radio}
          sub="Field hardware"
        />
        <StatCard
          label="Open Alerts"
          value={summary?.open_alerts ?? 0}
          icon={Bell}
          accent={summary?.critical_alerts ? 'bg-red-500/10 text-red-400' : undefined}
          sub={summary?.critical_alerts ? `${summary.critical_alerts} critical` : 'No critical alerts'}
        />
        <StatCard
          label="Workers On Site"
          value={summary?.workers_on_site ?? 0}
          icon={Users}
          sub="Active today"
        />
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-3">Recent Alerts</h2>
          <p className="text-sm text-slate-500">Open the Alerts tab for the full timeline →</p>
        </div>
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-3">Device Health</h2>
          <p className="text-sm text-slate-500">Open the Devices tab for all statuses →</p>
        </div>
      </div>
    </div>
  )
}
