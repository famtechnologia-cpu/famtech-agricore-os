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
        <div className="px-4 py-5 border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-brand rounded-lg flex items-center justify-center">
              <Tractor className="w-4 h-4 text-black" />
            </div>
            <div>
              <p className="text-sm font-display font-bold text-white leading-tight">Famtech</p>
              <p className="text-[10px] text-slate-500 font-mono leading-tight">AgriCore OS</p>
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
        <nav className="flex-1 px-3 py-3 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon, hasAlert }) => {
            const active = pathname.startsWith(href)
            const showBadge = hasAlert && unreadCount > 0

            return (
              <Link key={href} href={href}
                className={clsx(
                  'flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-all group',
                  active
                    ? 'bg-brand/10 text-brand'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                )}>
                <Icon className="w-4 h-4 shrink-0" />
                <span className="flex-1 font-medium">{label}</span>
                {showBadge && (
                  <span className="min-w-[18px] h-[18px] px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* User + logout */}
        <div className="px-3 py-4 border-t border-white/5">
          <div className="flex items-center gap-2.5 px-2 mb-2">
            <div className="w-7 h-7 rounded-full bg-brand/20 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-brand">
                {(user as { full_name?: string } | null)?.full_name?.charAt(0).toUpperCase() || 'U'}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-white truncate">
                {(user as { full_name?: string } | null)?.full_name || 'User'}
              </p>
              <p className="text-[10px] text-slate-500 font-mono truncate">
                {(user as { email?: string } | null)?.email || ''}
              </p>
            </div>
          </div>
          <button onClick={logout}
            className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs text-slate-500 hover:text-red-400 hover:bg-red-500/5 transition-colors">
            <LogOut className="w-3.5 h-3.5" />
            Sign out
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
