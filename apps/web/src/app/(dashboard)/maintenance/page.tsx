'use client'
import { useQuery } from '@tanstack/react-query'
import { maintenanceApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Wrench, Plus, Calendar } from 'lucide-react'
import clsx from 'clsx'
import { format, formatDistanceToNow } from 'date-fns'

interface MaintenanceEvent {
  id: string; device_id: string; type: string; description: string
  performed_at: string; next_due_at?: string; cost?: number; notes?: string
}

const TYPE_COLOR: Record<string, string> = {
  INSPECTION: 'text-blue-400 bg-blue-400/10',
  CALIBRATION: 'text-purple-400 bg-purple-400/10',
  REPAIR: 'text-red-400 bg-red-400/10',
  REPLACEMENT: 'text-orange-400 bg-orange-400/10',
  CLEANING: 'text-brand bg-brand/10',
  FIRMWARE_UPDATE: 'text-slate-300 bg-white/5',
}

export default function MaintenancePage() {
  const currentFarm = useStore((s) => s.currentFarm)

  const { data, isLoading } = useQuery<{ data: MaintenanceEvent[] }>({
    queryKey: ['maintenance', currentFarm?.id],
    queryFn: () => maintenanceApi.list(currentFarm!.id),
    enabled: !!currentFarm,
  })

  const events = data?.data || []
  const upcoming = events.filter(e => e.next_due_at && new Date(e.next_due_at) > new Date())

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">Maintenance</h1>
          <p className="text-sm text-slate-400 mt-0.5">{events.length} events logged · {upcoming.length} upcoming</p>
        </div>
        <button className="btn-primary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> Log Event
        </button>
      </div>

      {/* Upcoming due */}
      {upcoming.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-xs font-mono text-slate-400 uppercase tracking-wider">Upcoming</h2>
          {upcoming.map(e => (
            <div key={e.id} className="flex items-center gap-3 bg-yellow-400/5 border border-yellow-400/15 rounded-xl px-4 py-3">
              <Calendar className="w-4 h-4 text-yellow-400 shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-white">{e.description}</p>
                <p className="text-xs text-yellow-400 font-mono mt-0.5">
                  Due {formatDistanceToNow(new Date(e.next_due_at!), { addSuffix: true })} · {format(new Date(e.next_due_at!), 'dd MMM yyyy')}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* History */}
      <div className="space-y-2">
        <h2 className="text-xs font-mono text-slate-400 uppercase tracking-wider">History</h2>
        {isLoading ? (
          <div className="text-slate-500 font-mono text-sm">Loading...</div>
        ) : events.length === 0 ? (
          <div className="text-center py-16 text-slate-500">
            <Wrench className="w-10 h-10 mx-auto mb-3 opacity-20" />
            <p>No maintenance events logged.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {events.map(e => (
              <div key={e.id} className="card flex items-start gap-4">
                <span className={clsx('text-xs font-mono px-2 py-1 rounded-lg shrink-0 mt-0.5', TYPE_COLOR[e.type] || TYPE_COLOR.INSPECTION)}>
                  {e.type.replace('_', ' ')}
                </span>
                <div className="flex-1">
                  <p className="text-sm text-white">{e.description}</p>
                  {e.notes && <p className="text-xs text-slate-400 mt-0.5">{e.notes}</p>}
                  <p className="text-xs text-slate-500 font-mono mt-1">
                    {format(new Date(e.performed_at), 'dd MMM yyyy HH:mm')}
                    {e.cost ? ` · $${e.cost}` : ''}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
