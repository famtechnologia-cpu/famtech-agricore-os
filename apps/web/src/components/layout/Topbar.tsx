'use client'
import { usePathname } from 'next/navigation'
import { Search, Bell, Menu } from 'lucide-react'
import { useStore } from '@/lib/store/useStore'

export default function Topbar() {
  const pathname = usePathname()
  const currentFarm = useStore((s) => s.currentFarm)
  
  // Format pathname into breadcrumb
  const pathParts = pathname.split('/').filter(Boolean)
  const currentPage = pathParts.length > 0 
    ? pathParts[pathParts.length - 1].charAt(0).toUpperCase() + pathParts[pathParts.length - 1].slice(1)
    : 'Dashboard'

  return (
    <header className="h-16 px-6 flex items-center justify-between border-b border-white/5 bg-[#08090c]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="flex items-center gap-4">
        {/* Mobile menu button (placeholder) */}
        <button className="md:hidden p-2 text-slate-400 hover:text-white transition-colors">
          <Menu className="w-5 h-5" />
        </button>
        
        {/* Breadcrumb */}
        <div className="hidden md:flex items-center gap-2 text-sm font-medium">
          <span className="text-brand/80 font-display">{currentFarm?.name || 'Famtech'}</span>
          <span className="text-slate-600">/</span>
          <span className="text-white">{currentPage}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search farm..." 
            className="w-64 bg-[#0f1117] border border-white/10 rounded-full pl-9 pr-4 py-1.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-brand/50 transition-colors"
          />
        </div>

        {/* Notifications */}
        <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-brand rounded-full border-2 border-[#08090c]"></span>
        </button>
      </div>
    </header>
  )
}
