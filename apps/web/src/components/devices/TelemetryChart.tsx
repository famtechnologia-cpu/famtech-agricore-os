'use client'
import { useQuery } from '@tanstack/react-query'
import { deviceApi } from '@/lib/api/client'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts'
import { format } from 'date-fns'

interface Reading {
  id: string; metric: string; value: number; unit?: string; recorded_at: string
}

const METRIC_COLORS: Record<string, string> = {
  soil_moisture: '#10b981',
  soil_temp:     '#f59e0b',
  ph:            '#8b5cf6',
  do:            '#06b6d4',
  battery_pct:   '#6b7280',
  temperature:   '#ef4444',
  humidity:      '#3b82f6',
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#0f1117] border border-white/10 rounded-xl px-3 py-2 shadow-xl text-xs font-mono">
      <p className="text-slate-400 mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.dataKey}: {p.value.toFixed(2)} {p.payload?.unit || ''}
        </p>
      ))}
    </div>
  )
}

interface Props {
  farmId: string
  deviceId: string
  metrics?: string[]  // if omitted, auto-detect from data
}

export default function TelemetryChart({ farmId, deviceId, metrics }: Props) {
  const { data, isLoading } = useQuery<{ data: Reading[] }>({
    queryKey: ['readings', farmId, deviceId],
    queryFn: () => deviceApi.readings(farmId, deviceId, { limit: 96 }),
    refetchInterval: 30_000,
  })

  const readings = data?.data || []

  // Group readings by recorded_at timestamp, pivot into {time, metric1, metric2, ...}
  const grouped = readings.reduce<Record<string, Record<string, unknown>>>((acc, r) => {
    const ts = format(new Date(r.recorded_at), 'HH:mm dd/MM')
    if (!acc[ts]) acc[ts] = { time: ts }
    acc[ts][r.metric] = r.value
    acc[ts]['unit'] = r.unit
    return acc
  }, {})

  const chartData = Object.values(grouped).reverse()
  const detectedMetrics = metrics || Array.from(new Set(readings.map(r => r.metric)))

  if (isLoading) return (
    <div className="h-48 flex items-center justify-center text-slate-500 font-mono text-sm animate-pulse">
      Loading telemetry...
    </div>
  )

  if (!chartData.length) return (
    <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
      No readings yet — waiting for device to push telemetry.
    </div>
  )

  return (
    <div className="space-y-4">
      {detectedMetrics.map(metric => {
        const color = METRIC_COLORS[metric] || '#94a3b8'
        const hasData = chartData.some(d => (d as Record<string, unknown>)[metric] != null)
        if (!hasData) return null
        return (
          <div key={metric} className="card">
            <h3 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-3">
              {metric.replace(/_/g, ' ')}
            </h3>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10, fill: '#64748b', fontFamily: 'monospace' }}
                  tickLine={false} axisLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#64748b', fontFamily: 'monospace' }}
                  tickLine={false} axisLine={false}
                  width={40}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone" dataKey={metric}
                  stroke={color} strokeWidth={2} dot={false}
                  activeDot={{ r: 4, fill: color }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )
      })}
    </div>
  )
}
