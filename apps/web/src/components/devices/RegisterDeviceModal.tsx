'use client'
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deviceApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Radio, X, Copy, Check, Loader2 } from 'lucide-react'

const DEVICE_TYPES = [
  { value: 'SOILNODE',   label: '🌱 Soilnode — Soil sensor' },
  { value: 'WATCHTOWER', label: '📡 Watchtower — CCTV + weather' },
  { value: 'FEEDER',     label: '🪣 Feedpro — Auto feeder' },
  { value: 'AQUASENSE',  label: '🌊 Aquasense — Water quality buoy' },
  { value: 'FENCEGRID',  label: '🔒 Fencegrid — Perimeter sensor' },
  { value: 'WORKERTAG',  label: '👷 WorkerTag — Personnel tracker' },
  { value: 'HUB',        label: '🖥️  Hub — Edge gateway' },
]

interface Props { onClose: () => void }

export default function RegisterDeviceModal({ onClose }: Props) {
  const currentFarm = useStore(s => s.currentFarm)
  const qc = useQueryClient()

  const [name, setName] = useState('')
  const [type, setType] = useState('SOILNODE')
  const [serial, setSerial] = useState('')
  const [lat, setLat] = useState('')
  const [lng, setLng] = useState('')

  const [result, setResult] = useState<{ id: string; api_key: string } | null>(null)
  const [copied, setCopied] = useState(false)

  const register = useMutation({
    mutationFn: () => deviceApi.register(currentFarm!.id, {
      name, type, serial: serial || undefined,
      lat: lat ? parseFloat(lat) : undefined,
      lng: lng ? parseFloat(lng) : undefined,
    }),
    onSuccess: (res) => {
      setResult({ id: res.data.id, api_key: res.data.api_key })
      qc.invalidateQueries({ queryKey: ['devices', currentFarm?.id] })
    },
  })

  const copyKey = () => {
    if (!result) return
    navigator.clipboard.writeText(result.api_key)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-[#0f1117] border border-white/10 rounded-2xl shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-brand" />
            <h2 className="text-base font-semibold text-white">Register Device</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        {!result ? (
          <form onSubmit={(e) => { e.preventDefault(); register.mutate() }} className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5">Device Name *</label>
              <input
                required value={name} onChange={e => setName(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand/40 text-sm"
                placeholder="e.g. Soilnode North-01"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5">Device Type *</label>
              <select
                value={type} onChange={e => setType(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-brand/40 text-sm"
              >
                {DEVICE_TYPES.map(t => (
                  <option key={t.value} value={t.value} className="bg-[#0f1117]">{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5">Serial Number</label>
              <input
                value={serial} onChange={e => setSerial(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand/40 text-sm font-mono"
                placeholder="FT-SN-001 (optional)"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5">Latitude</label>
                <input
                  type="number" step="any" value={lat} onChange={e => setLat(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand/40 text-sm font-mono"
                  placeholder="7.3775"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5">Longitude</label>
                <input
                  type="number" step="any" value={lng} onChange={e => setLng(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand/40 text-sm font-mono"
                  placeholder="3.9470"
                />
              </div>
            </div>

            {register.isError && (
              <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                Registration failed. Check inputs and try again.
              </p>
            )}

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={onClose}
                className="flex-1 py-2.5 text-sm text-slate-400 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors">
                Cancel
              </button>
              <button type="submit" disabled={register.isPending || !name}
                className="flex-1 btn-primary py-2.5 text-sm disabled:opacity-50 flex items-center justify-center gap-2">
                {register.isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Registering...</> : 'Register Device'}
              </button>
            </div>
          </form>
        ) : (
          /* Success state — show API key */
          <div className="p-6 space-y-4">
            <div className="bg-brand/10 border border-brand/20 rounded-xl p-4">
              <p className="text-brand font-semibold text-sm mb-1">✓ Device registered successfully</p>
              <p className="text-slate-400 text-xs">Copy the API key below — it will NOT be shown again.</p>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5">Device ID</label>
              <p className="font-mono text-xs text-slate-300 bg-white/5 border border-white/10 rounded-lg px-3 py-2 break-all">{result.id}</p>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5">API Key</label>
              <div className="flex items-center gap-2">
                <p className="flex-1 font-mono text-xs text-white bg-white/5 border border-white/10 rounded-lg px-3 py-2 break-all">{result.api_key}</p>
                <button onClick={copyKey}
                  className="shrink-0 p-2 bg-brand/10 border border-brand/20 rounded-lg hover:bg-brand/20 transition-colors">
                  {copied ? <Check className="w-4 h-4 text-brand" /> : <Copy className="w-4 h-4 text-brand" />}
                </button>
              </div>
            </div>

            <div className="bg-white/3 border border-white/8 rounded-xl p-4 font-mono text-xs text-slate-400 space-y-1">
              <p className="text-slate-300">Flash to device firmware:</p>
              <p>DEVICE_ID=<span className="text-brand">{result.id}</span></p>
              <p>API_KEY=<span className="text-yellow-400">{result.api_key.slice(0, 12)}...</span></p>
              <p>HUB_URL=<span className="text-slate-300">http://hub.local:8001</span></p>
            </div>

            <button onClick={onClose} className="w-full btn-primary py-2.5 text-sm">Done</button>
          </div>
        )}
      </div>
    </div>
  )
}
