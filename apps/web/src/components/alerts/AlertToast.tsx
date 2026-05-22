'use client'
import { useEffect, useState } from 'react'
import { AlertTriangle, X, ChevronRight } from 'lucide-react'
import { useRouter } from 'next/navigation'
import clsx from 'clsx'

interface ToastProps {
  title: string
  severity: string
  onDismiss: () => void
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: 'border-red-500/40 bg-red-500/10',
  HIGH:     'border-orange-500/40 bg-orange-500/10',
  MEDIUM:   'border-yellow-500/40 bg-yellow-500/10',
  LOW:      'border-brand/30 bg-brand/10',
  INFO:     'border-slate-500/30 bg-white/5',
}

const SEVERITY_ICON_COLOR: Record<string, string> = {
  CRITICAL: 'text-red-400', HIGH: 'text-orange-400',
  MEDIUM: 'text-yellow-400', LOW: 'text-brand', INFO: 'text-slate-400',
}

/**
 * Alert toast that auto-dismisses after 6 seconds.
 * Includes a slide-in animation and "View Alerts" link.
 */
export function AlertToast({ title, severity, onDismiss }: ToastProps) {
  const router = useRouter()
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Trigger slide-in after paint
    requestAnimationFrame(() => setVisible(true))
    const timer = setTimeout(() => { setVisible(false); setTimeout(onDismiss, 300) }, 6_000)
    return () => clearTimeout(timer)
  }, [onDismiss])

  const handleView = () => { router.push('/alerts'); onDismiss() }

  return (
    <div className={clsx(
      'fixed bottom-6 right-6 z-50 w-72 rounded-xl border shadow-2xl p-4',
      'transition-all duration-300',
      visible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0',
      SEVERITY_COLORS[severity] || SEVERITY_COLORS.INFO
    )}>
      <div className="flex items-start gap-3">
        <AlertTriangle className={clsx('w-4 h-4 mt-0.5 shrink-0', SEVERITY_ICON_COLOR[severity] || 'text-slate-400')} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">{severity} Alert</p>
          <p className="text-sm text-white font-medium mt-0.5 truncate">{title}</p>
        </div>
        <button onClick={onDismiss} className="text-slate-500 hover:text-white transition-colors shrink-0">
          <X className="w-4 h-4" />
        </button>
      </div>
      <button onClick={handleView}
        className="mt-3 w-full flex items-center justify-center gap-1 text-xs text-slate-400 hover:text-white transition-colors">
        View Alerts <ChevronRight className="w-3 h-3" />
      </button>
    </div>
  )
}
