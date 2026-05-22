'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useStore } from '@/lib/store/useStore'
import { useAlertSocket } from '@/lib/ws/useAlertSocket'
import { AlertToast } from '@/components/alerts/AlertToast'
import { useState, useEffect } from 'react'
import clsx from 'clsx'
import {
  LayoutDashboard, Radio, BellRing, Cog, WrenchIcon,
  FileBarChart2, Map, Users, LogOut, ChevronDown, Tractor
} from 'lucide-react'

const NAV = [
  { href: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
  { href: '/devices',     label: 'Devices',      icon: Radio },
  { href: '/alerts',      label: 'Alerts',       icon: BellRing,    hasAlert: true },
  { href: '/rules',       label: 'Rules',        icon: Cog },
  { href: '/maintenance', label: 'Maintenance',  icon: WrenchIcon },
  { href: '/workers',     label: 'Workers',      icon: Users },
  { href: '/map',         label: 'Farm Map',     icon: Map },
  { href: '/reports',     label: 'Reports',      icon: FileBarChart2 },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { logout, user, farms, currentFarm, setCurrentFarm } = useStore(s => ({
    logout: s.logout, user: s.user, farms: s.farms,
    currentFarm: s.currentFarm, setCurrentFarm: s.setCurrentFarm
  }))
  const [farmOpen, setFarmOpen] = useState(false)

  // Live alert socket
  const { unreadCount, latestAlert, clearUnread } = useAlertSocket()
  const [toast, setToast] = useState<{ title: string; severity: string } | null>(null)

  useEffect(() => {
    if (latestAlert) setToast({ title: latestAlert.title, severity: latestAlert.severity })
  }, [latestAlert])

  // Clear badge when user visits alerts page
  useEffect(() => {
    if (pathname === '/alerts') clearUnread()
  }, [pathname, clearUnread])

  return (
    <>
      <aside className="w-56 flex flex-col bg-[#0a0c10] border-r border-white/5 min-h-screen">
        {/* Logo */}
        <div className="px-5 py-6 border-b border-white/5 bg-gradient-to-b from-white/[0.02] to-transparent">
          <div className="flex items-center gap-3 relative">
            <div className="absolute inset-0 bg-brand/20 blur-xl rounded-full opacity-50" />
            <div className="w-8 h-8 bg-brand rounded-xl flex items-center justify-center relative shadow-[0_0_15px_rgba(16,185,129,0.3)]">
              <Tractor className="w-4 h-4 text-black" />
            </div>
            <div className="relative">
              <p className="text-base font-display font-bold text-white tracking-wide">Famtech</p>
              <p className="text-[10px] text-brand font-mono font-medium tracking-widest uppercase">AgriCore OS</p>
            </div>
          </div>
        </div>

        {/* Farm switcher */}
        {farms && farms.length > 0 && (
          <div className="px-3 py-2 border-b border-white/5">
            <button onClick={() => setFarmOpen(o => !o)}
              className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-white/5 text-left transition-colors">
              <div className="min-w-0">
                <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Current Farm</p>
                <p className="text-xs text-white font-medium truncate">{currentFarm?.name || 'Select farm'}</p>
              </div>
              <ChevronDown className={clsx('w-3.5 h-3.5 text-slate-500 transition-transform shrink-0', farmOpen && 'rotate-180')} />
            </button>
            {farmOpen && (
              <div className="mt-1 space-y-0.5">
                {(farms as Array<{id: string; name: string}>).map((f) => (
                  <button key={f.id} onClick={() => { setCurrentFarm({ ...f, timezone: (f as { timezone?: string }).timezone || 'UTC' }); setFarmOpen(false) }}
                    className={clsx('w-full text-left px-2 py-1.5 rounded-lg text-xs transition-colors',
                      currentFarm?.id === f.id ? 'bg-brand/10 text-brand' : 'text-slate-400 hover:bg-white/5 hover:text-white'
                    )}>
                    {f.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider px-2 mb-2">Main Menu</div>
          {NAV.map(({ href, label, icon: Icon, hasAlert }) => {
            const active = pathname.startsWith(href)
            const showBadge = hasAlert && unreadCount > 0

            return (
              <Link key={href} href={href}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-300 group relative',
                  active
                    ? 'bg-brand/10 text-brand font-semibold shadow-[inset_0_0_12px_rgba(16,185,129,0.1)]'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                )}>
                {active && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-brand rounded-r-full shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                )}
                <Icon className={clsx("w-4 h-4 shrink-0 transition-transform duration-300", !active && "group-hover:translate-x-1", active && "drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]")} />
                <span className="flex-1">{label}</span>
                {showBadge && (
                  <span className="min-w-[20px] h-[20px] px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.5)]">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* User + logout */}
        <div className="p-4 border-t border-white/5 bg-gradient-to-t from-black/20 to-transparent">
          <div className="flex items-center gap-3 p-2 bg-white/5 rounded-xl border border-white/5 mb-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand to-brand-dark flex items-center justify-center shrink-0 shadow-lg">
              <span className="text-sm font-bold text-white">
                {(user as { full_name?: string } | null)?.full_name?.charAt(0).toUpperCase() || 'U'}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-white truncate">
                {(user as { full_name?: string } | null)?.full_name || 'User'}
              </p>
              <p className="text-[10px] text-brand/80 font-mono truncate">
                {(user as { email?: string } | null)?.email || ''}
              </p>
            </div>
          </div>
          <button onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all duration-300 group">
            <LogOut className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Secure Sign Out
          </button>
        </div>
      </aside>

      {/* Alert toast (bottom-right) */}
      {toast && (
        <AlertToast
          key={toast.title + Date.now()}
          title={toast.title}
          severity={toast.severity}
          onDismiss={() => setToast(null)}
        />
      )}
    </>
  )
}
