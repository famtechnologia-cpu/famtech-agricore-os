'use client'
import { useQuery } from '@tanstack/react-query'
import { farmApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Radio, Bell, AlertTriangle, Users, Wifi, Activity, ArrowUpRight, ArrowDownRight, Clock } from 'lucide-react'
import clsx from 'clsx'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface Summary {
  farm: { id: string; name: string; timezone: string }
  device_count: number
  online_devices: number
  open_alerts: number
  critical_alerts: number
  workers_on_site: number
  last_updated: string
}

// Mock data for the telemetry chart
const TELEMETRY_DATA = [
  { time: '00:00', moisture: 42, temp: 18 },
  { time: '04:00', moisture: 40, temp: 16 },
  { time: '08:00', moisture: 38, temp: 22 },
  { time: '12:00', moisture: 35, temp: 28 },
  { time: '16:00', moisture: 32, temp: 26 },
  { time: '20:00', moisture: 45, temp: 20 }, // Irrigation triggered
  { time: '24:00', moisture: 44, temp: 19 },
]

function StatCard({ label, value, sub, icon: Icon, accent, trend }: {
  label: string; value: number | string; sub?: string; icon: React.ElementType; accent?: string; trend?: { value: string, up: boolean }
}) {
  return (
    <div className="card flex flex-col justify-between animate-fade-in-up" style={{ animationFillMode: 'both' }}>
      <div className="flex items-start justify-between mb-4">
        <div className={clsx('p-3 rounded-xl shadow-inner', accent || 'bg-brand/10 text-brand')}>
          <Icon className="w-6 h-6" />
        </div>
        {trend && (
          <span className={clsx("flex items-center gap-1 text-xs font-mono font-medium px-2 py-1 rounded-full", trend.up ? "bg-brand/10 text-brand" : "bg-red-500/10 text-red-400")}>
            {trend.up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {trend.value}
          </span>
        )}
      </div>
      <div>
        <h3 className="text-3xl font-display font-bold text-white mb-1">{value}</h3>
        <p className="text-sm font-medium text-slate-400">{label}</p>
        {sub && <p className="text-xs text-slate-500 mt-1 font-mono">{sub}</p>}
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
      <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-400 animate-fade-in-up">
        <div className="relative">
          <Activity className="w-16 h-16 opacity-20" />
          <div className="absolute inset-0 bg-brand/20 blur-2xl rounded-full opacity-50 animate-pulse" />
        </div>
        <p className="font-mono text-sm tracking-wide">SYSTEM STANDBY. SELECT A FARM.</p>
      </div>
    )
  }

  if (isLoading) {
    return <div className="p-8 text-brand font-mono text-sm animate-pulse tracking-widest">INITIALIZING TELEMETRY...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 animate-fade-in-up">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-display font-bold text-white tracking-tight">{summary?.farm.name}</h1>
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-brand/20 text-brand text-[10px] font-mono font-bold uppercase border border-brand/30">
              <span className="w-1.5 h-1.5 rounded-full bg-brand animate-ping" />
              Live Sync
            </span>
          </div>
          <p className="text-sm text-slate-400 font-mono">
            Timezone: {summary?.farm.timezone} • Last updated: {summary ? new Date(summary.last_updated).toLocaleTimeString() : '—'}
          </p>
        </div>
        <span className={clsx(
          'flex items-center gap-2 text-xs font-mono font-bold px-4 py-2 rounded-lg border shadow-lg',
          summary?.critical_alerts 
            ? 'bg-red-500/10 text-red-400 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.2)]' 
            : 'bg-brand/10 text-brand border-brand/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
        )}>
          {summary?.critical_alerts ? <AlertTriangle className="w-4 h-4 animate-pulse" /> : <Wifi className="w-4 h-4" />}
          {summary?.critical_alerts ? `${summary.critical_alerts} CRITICAL ALERTS` : 'SYSTEM NOMINAL'}
        </span>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          label="Devices Online"
          value={`${summary?.online_devices ?? 0} / ${summary?.device_count ?? 0}`}
          icon={Radio}
          sub="Active field hardware"
          trend={{ value: '100%', up: true }}
        />
        <StatCard
          label="Open Alerts"
          value={summary?.open_alerts ?? 0}
          icon={Bell}
          accent={summary?.critical_alerts ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'}
          sub={summary?.critical_alerts ? `${summary.critical_alerts} requiring immediate action` : 'No critical alerts'}
          trend={summary?.open_alerts && summary.open_alerts > 0 ? { value: '+2', up: false } : undefined}
        />
        <StatCard
          label="Workers On Site"
          value={summary?.workers_on_site ?? 0}
          icon={Users}
          sub="Checked in today"
          trend={{ value: 'Stable', up: true }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <div className="card lg:col-span-2 animate-fade-in-up" style={{ animationDelay: '0.1s', animationFillMode: 'both' }}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-display font-semibold text-white">24H Field Telemetry</h2>
              <p className="text-xs text-slate-400 font-mono mt-1">Average Soil Moisture & Temp across all sectors</p>
            </div>
            <select className="bg-[#08090c] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-brand/50">
              <option>All Sectors</option>
              <option>North Field</option>
              <option>South Orchard</option>
            </select>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={TELEMETRY_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMoisture" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="time" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f1117', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' }}
                  itemStyle={{ fontSize: '14px', fontWeight: 500 }}
                  labelStyle={{ color: '#94a3b8', marginBottom: '4px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="moisture" stroke="#0ea5e9" strokeWidth={3} fillOpacity={1} fill="url(#colorMoisture)" name="Moisture (%)" />
                <Area type="monotone" dataKey="temp" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorTemp)" name="Temperature (°C)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="card flex flex-col animate-fade-in-up" style={{ animationDelay: '0.2s', animationFillMode: 'both' }}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-display font-semibold text-white">Activity Feed</h2>
            <button className="text-xs font-mono text-brand hover:text-brand-light transition-colors">View All</button>
          </div>
          <div className="flex-1 overflow-y-auto pr-2 space-y-4">
            {/* Feed Item 1 */}
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-brand/10 border border-brand/20 flex items-center justify-center shrink-0 mt-1">
                <Wifi className="w-3.5 h-3.5 text-brand" />
              </div>
              <div>
                <p className="text-sm text-slate-200">SoilNode Alpha came online</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <p className="text-[10px] text-slate-500 font-mono">2 mins ago • North Field</p>
                </div>
              </div>
            </div>
            
            {/* Feed Item 2 */}
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center shrink-0 mt-1">
                <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              </div>
              <div>
                <p className="text-sm text-slate-200">Low Moisture Alert Triggered</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <p className="text-[10px] text-slate-500 font-mono">45 mins ago • South Orchard</p>
                </div>
              </div>
            </div>
            
            {/* Feed Item 3 */}
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0 mt-1">
                <Activity className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-slate-200">Irrigation Sequence Initiated</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <p className="text-[10px] text-slate-500 font-mono">1 hour ago • Auto-Rule</p>
                </div>
              </div>
            </div>

            {/* Feed Item 4 */}
            <div className="flex gap-3 opacity-60">
              <div className="w-8 h-8 rounded-full bg-slate-500/10 border border-slate-500/20 flex items-center justify-center shrink-0 mt-1">
                <Users className="w-3.5 h-3.5 text-slate-400" />
              </div>
              <div>
                <p className="text-sm text-slate-200">Worker David checked in</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <p className="text-[10px] text-slate-500 font-mono">3 hours ago</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
