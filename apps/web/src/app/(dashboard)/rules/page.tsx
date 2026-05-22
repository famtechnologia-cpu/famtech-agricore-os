'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ruleApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { Settings2, ToggleLeft, ToggleRight, Plus, History } from 'lucide-react'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import CreateRuleModal from '@/components/rules/CreateRuleModal'

interface Rule {
  id: string; name: string; enabled: boolean; trigger_type: string
  trigger_config: Record<string, unknown>; action_json: Record<string, unknown>
  last_fired_at?: string; created_at: string
}

function RuleCard({ rule, farmId }: { rule: Rule; farmId: string }) {
  const qc = useQueryClient()
  const toggle = useMutation({
    mutationFn: () => ruleApi.toggle(farmId, rule.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules', farmId] }),
  })

  const cfg = rule.trigger_config
  const action = rule.action_json

  return (
    <div className={clsx('card transition-all', !rule.enabled && 'opacity-50')}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-slate-500 bg-white/5 px-2 py-0.5 rounded">
              {rule.trigger_type}
            </span>
            {rule.last_fired_at && (
              <span className="text-xs text-slate-500">
                Last fired {formatDistanceToNow(new Date(rule.last_fired_at), { addSuffix: true })}
              </span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-white">{rule.name}</h3>

          {/* Trigger summary */}
          <div className="mt-2 text-xs font-mono text-slate-400 bg-white/3 rounded-lg px-3 py-2 space-y-1">
            <p className="text-slate-500">IF</p>
            <p className="text-white">
              {String(cfg.metric || '—')} {String(cfg.operator || '')} {String(cfg.value ?? '')}
            </p>
            <p className="text-slate-500 mt-1">THEN</p>
            {Array.isArray(action.notify) && (
              <p className="text-white">Notify via {(action.notify as string[]).join(', ')}</p>
            )}
            {Boolean(action.create_alert) && typeof action.create_alert === 'object' && (
              <p className="text-white">
                Create {String((action.create_alert as Record<string, unknown>).severity)} alert
              </p>
            )}
          </div>
        </div>

        {/* Toggle */}
        <button onClick={() => toggle.mutate()} disabled={toggle.isPending}
          className={clsx('transition-colors mt-1', rule.enabled ? 'text-brand hover:text-brand/70' : 'text-slate-600 hover:text-slate-400')}>
          {rule.enabled ? <ToggleRight className="w-7 h-7" /> : <ToggleLeft className="w-7 h-7" />}
        </button>
      </div>
    </div>
  )
}

export default function RulesPage() {
  const currentFarm = useStore((s) => s.currentFarm)
  const [showModal, setShowModal] = useState(false)

  const { data, isLoading } = useQuery<{ data: Rule[] }>({
    queryKey: ['rules', currentFarm?.id],
    queryFn: () => ruleApi.list(currentFarm!.id),
    enabled: !!currentFarm,
  })

  const rules = data?.data || []
  const enabled = rules.filter(r => r.enabled).length

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">Rules Engine</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {enabled} of {rules.length} rules active
          </p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> New Rule
        </button>
      </div>

      {showModal && <CreateRuleModal onClose={() => setShowModal(false)} />}

      <div className="bg-brand/5 border border-brand/15 rounded-xl px-4 py-3 text-sm text-slate-300">
        <strong className="text-brand">Human override always available.</strong> Toggle any rule off instantly to pause automation without deleting it.
      </div>

      {isLoading ? (
        <div className="text-slate-500 font-mono text-sm">Loading rules...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rules.map(r => <RuleCard key={r.id} rule={r} farmId={currentFarm!.id} />)}
          {rules.length === 0 && (
            <div className="col-span-full text-center py-16 text-slate-500">
              <Settings2 className="w-10 h-10 mx-auto mb-3 opacity-20" />
              <p>No rules configured yet.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
