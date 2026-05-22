'use client'
import { useQuery } from '@tanstack/react-query'
import { maintenanceApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Wrench, Plus, Calendar } from 'lucide-react'
import clsx from 'clsx'
import { format, formatDistanceToNow } from 'date-fns'
import { useState } from 'react'
import LogMaintenanceModal from '@/components/maintenance/LogMaintenanceModal'

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
  const [showModal, setShowModal] = useState(false)

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
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> Log Event
        </button>
      </div>

      {showModal && <LogMaintenanceModal onClose={() => setShowModal(false)} />}

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
          <div className="bg-[#0a0c10] border border-white/5 rounded-xl overflow-hidden mt-4">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-white/[0.02] border-b border-white/5 text-slate-400 font-mono text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Description</th>
                  <th className="px-4 py-3 font-medium">Notes</th>
                  <th className="px-4 py-3 font-medium">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {events.map(e => (
                  <tr key={e.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 text-slate-300 font-mono text-xs">
                      {format(new Date(e.performed_at), 'dd MMM yyyy HH:mm')}
                    </td>
                    <td className="px-4 py-3">
                      <span className={clsx('text-[10px] font-mono px-2 py-0.5 rounded-full border border-white/5', TYPE_COLOR[e.type] || TYPE_COLOR.INSPECTION)}>
                        {e.type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white font-medium">{e.description}</td>
                    <td className="px-4 py-3 text-slate-400 truncate max-w-[200px]">{e.notes || '—'}</td>
                    <td className="px-4 py-3 text-slate-400 font-mono">
                      {e.cost ? `$${e.cost.toFixed(2)}` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
