'use client'
import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useStore } from '@/lib/store/useStore'
import { useFarmSocket, onFarmEvent } from '@/lib/ws/farmSocket'
import { Users, MapPin, Clock, Wifi } from 'lucide-react'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import axios from '@/lib/api/client'

interface WorkerStatus {
  id: string; name: string; role: string; active: boolean
  on_site: boolean; last_seen_at?: string
  current_sector_id?: string; lat?: number; lng?: number
}

function WorkerCard({ worker }: { worker: WorkerStatus }) {
  return (
    <div className={clsx('card transition-all', !worker.active && 'opacity-40')}>
      <div className="flex items-start gap-3">
        <div className={clsx(
          'w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0',
          worker.on_site ? 'bg-brand/20 text-brand' : 'bg-white/5 text-slate-400'
        )}>
          {worker.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-white truncate">{worker.name}</h3>
            <span className={clsx(
              'text-xs font-mono px-2 py-0.5 rounded-full border shrink-0',
              worker.on_site
                ? 'bg-brand/10 text-brand border-brand/20'
                : 'bg-white/5 text-slate-500 border-white/5'
            )}>
              {worker.on_site ? '● On Site' : '○ Off Site'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">{worker.role}</p>
          {worker.last_seen_at && (
            <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-500">
              <Clock className="w-3 h-3" />
              {formatDistanceToNow(new Date(worker.last_seen_at), { addSuffix: true })}
            </div>
          )}
          {worker.lat && worker.lng && (
            <div className="flex items-center gap-1.5 mt-1 text-xs text-slate-500">
              <MapPin className="w-3 h-3" />
              {worker.lat.toFixed(4)}, {worker.lng.toFixed(4)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function WorkersPage() {
  const currentFarm = useStore(s => s.currentFarm)
  const qc = useQueryClient()

  // Connect WebSocket for live updates
  useFarmSocket()

  // Refresh worker list on real-time events
  useEffect(() => {
    return onFarmEvent('DEVICE_UPDATED', () => {
      qc.invalidateQueries({ queryKey: ['workers', currentFarm?.id] })
    })
  }, [currentFarm?.id, qc])

  const { data, isLoading } = useQuery<WorkerStatus[]>({
    queryKey: ['workers', currentFarm?.id],
    queryFn: async () => {
      const res = await axios.get(`/farms/${currentFarm!.id}/workers`)
      return res.data
    },
    enabled: !!currentFarm,
    refetchInterval: 30_000,
  })

  const workers = data || []
  const onSite = workers.filter(w => w.on_site).length
  const total = workers.filter(w => w.active).length

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">Workers</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {onSite} on site · {total} active
          </p>
        </div>
        <button className="btn-primary flex items-center gap-2 text-sm">
          <Users className="w-4 h-4" /> Add Worker
        </button>
      </div>

      {/* On-site summary */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-brand/8 border border-brand/15 px-4 py-3">
          <p className="text-2xl font-display font-bold text-brand">{onSite}</p>
          <p className="text-xs text-slate-400 mt-0.5">Currently On Site</p>
        </div>
        <div className="rounded-xl bg-white/3 border border-white/5 px-4 py-3">
          <p className="text-2xl font-display font-bold text-slate-300">{total - onSite}</p>
          <p className="text-xs text-slate-400 mt-0.5">Off Site / Untracked</p>
        </div>
      </div>

      {isLoading ? (
        <div className="text-slate-500 font-mono text-sm">Loading workers...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {workers.map(w => <WorkerCard key={w.id} worker={w} />)}
          {workers.length === 0 && (
            <div className="col-span-full text-center py-16 text-slate-500">
              <Users className="w-10 h-10 mx-auto mb-3 opacity-20" />
              <p>No workers registered. Click "Add Worker" to get started.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
