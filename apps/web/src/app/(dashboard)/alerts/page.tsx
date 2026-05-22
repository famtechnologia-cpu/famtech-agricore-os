'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { alertApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Bell, AlertTriangle, Info, Check, Eye } from 'lucide-react'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'

interface Alert {
  id: string; title: string; message: string; severity: string
  type: string; status: string; created_at: string
  device_id?: string; sector_id?: string; context_json?: Record<string, unknown>
}

const SEV_CONFIG: Record<string, { color: string; bg: string; border: string; icon: React.ElementType }> = {
  CRITICAL: { color: 'text-red-400',    bg: 'bg-red-500/8',    border: 'border-red-500/20',    icon: AlertTriangle },
  HIGH:     { color: 'text-orange-400', bg: 'bg-orange-500/8', border: 'border-orange-500/20', icon: AlertTriangle },
  MEDIUM:   { color: 'text-yellow-400', bg: 'bg-yellow-500/8', border: 'border-yellow-500/20', icon: Info },
  LOW:      { color: 'text-slate-400',  bg: 'bg-white/3',      border: 'border-white/6',       icon: Info },
  INFO:     { color: 'text-brand',      bg: 'bg-brand/8',      border: 'border-brand/20',      icon: Info },
}

const STATUS_FILTERS = ['ALL', 'OPEN', 'ACKNOWLEDGED', 'RESOLVED']
const SEV_FILTERS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

function AlertRow({ alert, farmId }: { alert: Alert; farmId: string }) {
  const qc = useQueryClient()
  const cfg = SEV_CONFIG[alert.severity] || SEV_CONFIG.LOW
  const Icon = cfg.icon

  const acknowledge = useMutation({
    mutationFn: () => alertApi.acknowledge(farmId, alert.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts', farmId] }),
  })
  const resolve = useMutation({
    mutationFn: () => alertApi.resolve(farmId, alert.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts', farmId] }),
  })

  return (
    <div className={clsx('rounded-xl border p-4 transition-all', cfg.bg, cfg.border)}>
      <div className="flex items-start gap-3">
        <div className={clsx('p-1.5 rounded-lg mt-0.5', `bg-current/10`)}>
          <Icon className={clsx('w-4 h-4', cfg.color)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className={clsx('text-xs font-mono font-bold uppercase tracking-wider', cfg.color)}>
                {alert.severity}
              </span>
              <h3 className="text-sm font-semibold text-white mt-0.5">{alert.title}</h3>
              <p className="text-sm text-slate-400 mt-0.5 leading-relaxed">{alert.message}</p>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <span className={clsx(
                'text-xs font-mono px-2 py-0.5 rounded-full border',
                alert.status === 'OPEN' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                alert.status === 'ACKNOWLEDGED' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                'bg-brand/10 text-brand border-brand/20'
              )}>
                {alert.status}
              </span>
              <span className="text-xs text-slate-500">
                {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
              </span>
            </div>
          </div>

          {alert.status === 'OPEN' && (
            <div className="flex gap-2 mt-3">
              <button onClick={() => acknowledge.mutate()}
                disabled={acknowledge.isPending}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-colors disabled:opacity-50">
                <Eye className="w-3 h-3" /> Acknowledge
              </button>
              <button onClick={() => resolve.mutate()}
                disabled={resolve.isPending}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-brand/10 text-brand border border-brand/20 hover:bg-brand/20 transition-colors disabled:opacity-50">
                <Check className="w-3 h-3" /> Resolve
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AlertsPage() {
  const currentFarm = useStore((s) => s.currentFarm)
  const [statusFilter, setStatusFilter] = useState('OPEN')
  const [sevFilter, setSevFilter] = useState('ALL')

  const { data, isLoading } = useQuery<{ data: Alert[] }>({
    queryKey: ['alerts', currentFarm?.id, statusFilter, sevFilter],
    queryFn: () => alertApi.list(currentFarm!.id, {
      status: statusFilter === 'ALL' ? undefined : statusFilter,
      severity: sevFilter === 'ALL' ? undefined : sevFilter,
    }),
    enabled: !!currentFarm,
    refetchInterval: 20_000,
  })

  const alerts = data?.data || []
  const critical = alerts.filter(a => a.severity === 'CRITICAL' && a.status === 'OPEN').length

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">Alerts</h1>
          <p className="text-sm text-slate-400 mt-0.5">Incident timeline and alert management</p>
        </div>
        {critical > 0 && (
          <span className="flex items-center gap-1.5 text-sm font-mono px-3 py-1.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 animate-pulse">
            <AlertTriangle className="w-4 h-4" /> {critical} CRITICAL
          </span>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex gap-1 bg-white/3 rounded-lg p-1">
          {STATUS_FILTERS.map(f => (
            <button key={f} onClick={() => setStatusFilter(f)}
              className={clsx('px-3 py-1 rounded-md text-xs font-mono transition-colors',
                statusFilter === f ? 'bg-brand/20 text-brand' : 'text-slate-400 hover:text-white')}>
              {f}
            </button>
          ))}
        </div>
        <div className="flex gap-1 bg-white/3 rounded-lg p-1">
          {SEV_FILTERS.map(f => (
            <button key={f} onClick={() => setSevFilter(f)}
              className={clsx('px-3 py-1 rounded-md text-xs font-mono transition-colors',
                sevFilter === f ? 'bg-brand/20 text-brand' : 'text-slate-400 hover:text-white')}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Alert list */}
      {isLoading ? (
        <div className="text-slate-500 font-mono text-sm">Loading alerts...</div>
      ) : (
        <div className="space-y-3">
          {alerts.map(a => <AlertRow key={a.id} alert={a} farmId={currentFarm!.id} />)}
          {alerts.length === 0 && (
            <div className="text-center py-16 text-slate-500">
              <Bell className="w-10 h-10 mx-auto mb-3 opacity-20" />
              <p>No alerts match the current filter.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
