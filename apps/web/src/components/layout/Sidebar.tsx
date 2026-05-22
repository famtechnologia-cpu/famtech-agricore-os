'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useStore } from '@/lib/store/useStore'
import {
  LayoutDashboard, Radio, Bell, Settings2,
  Wrench, BarChart3, ShieldCheck, Users,
  Wifi, WifiOff, ChevronDown, LogOut
} from 'lucide-react'
import clsx from 'clsx'

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/map', label: 'Farm Map', icon: LayoutDashboard },
  { href: '/devices', label: 'Devices', icon: Radio },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/rules', label: 'Rules', icon: Settings2 },
  { href: '/maintenance', label: 'Maintenance', icon: Wrench },
  { href: '/reports', label: 'Reports', icon: BarChart3 },
  { href: '/security', label: 'Security', icon: ShieldCheck },
  { href: '/workers', label: 'Workers', icon: Users },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, currentFarm, isOnline, logout } = useStore()

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 bg-[#0b0d10] border-r border-white/5 flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/5">
        <span className="font-display font-bold text-lg text-white">Famtech</span>
        <span className="text-brand font-display font-bold text-lg"> AgriCore</span>
      </div>

      {/* Farm selector */}
      {currentFarm && (
        <div className="px-4 py-3 border-b border-white/5">
          <button className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-white/3 hover:bg-white/5 transition-colors text-left">
            <div>
              <p className="text-xs text-slate-500 font-mono uppercase tracking-wider">Active Farm</p>
              <p className="text-sm text-white font-medium truncate">{currentFarm.name}</p>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
          </button>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href)
          return (
            <Link key={href} href={href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                active ? 'bg-brand/10 text-brand font-medium' : 'text-slate-400 hover:text-white hover:bg-white/4'
              )}>
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer: online status + user */}
      <div className="px-4 py-4 border-t border-white/5 space-y-3">
        <div className={clsx('flex items-center gap-2 text-xs font-mono', isOnline ? 'text-brand' : 'text-slate-500')}>
          {isOnline ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
          {isOnline ? 'Connected' : 'Offline'}
        </div>
        {user && (
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-white font-medium truncate">{user.full_name}</p>
              <p className="text-xs text-slate-500 truncate">{user.email}</p>
            </div>
            <button onClick={logout} className="text-slate-500 hover:text-red-400 transition-colors p-1">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}
