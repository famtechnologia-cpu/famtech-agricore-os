import dynamic from 'next/dynamic'

// Leaflet is browser-only — use dynamic import with no SSR
const FarmMap = dynamic(() => import('@/components/map/FarmMap'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full text-slate-500 font-mono text-sm animate-pulse">
      Loading map...
    </div>
  ),
})

export default function MapPage() {
  return (
    <div className="p-6 h-screen flex flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-display font-bold text-white">Farm Map</h1>
        <p className="text-sm text-slate-400 mt-0.5">Live device positions and farm boundary</p>
      </div>
      <div className="flex-1 rounded-xl overflow-hidden border border-white/5 min-h-0">
        <FarmMap />
      </div>
    </div>
  )
}
