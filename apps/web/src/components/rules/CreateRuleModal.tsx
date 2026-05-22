'use client'
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ruleApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { X, Save, ArrowRight } from 'lucide-react'

export default function CreateRuleModal({ onClose }: { onClose: () => void }) {
  const currentFarm = useStore(s => s.currentFarm)
  const qc = useQueryClient()

  const [name, setName] = useState('')
  const [metric, setMetric] = useState('soil_moisture')
  const [operator, setOperator] = useState('<')
  const [value, setValue] = useState('')
  
  const [actionType, setActionType] = useState('create_alert')
  const [severity, setSeverity] = useState('HIGH')

  const create = useMutation({
    mutationFn: async () => {
      if (!currentFarm) throw new Error('No farm selected')
      
      const payload = {
        name,
        enabled: true,
        trigger_type: 'telemetry_threshold',
        trigger_config: {
          metric,
          operator,
          value: parseFloat(value),
        },
        action_json: actionType === 'create_alert' 
          ? { create_alert: { severity, title: name } }
          : { notify: ['email'] }
      }

      await ruleApi.create(currentFarm.id, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['rules', currentFarm?.id] })
      onClose()
    }
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0a0c10] border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-slide-up">
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <h2 className="text-lg font-display font-bold text-white">Create Automation Rule</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-6">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">Rule Name</label>
            <input 
              type="text" 
              value={name} 
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Low Soil Moisture Warning" 
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand"
            />
          </div>

          <div className="space-y-3 bg-white/3 border border-white/5 p-4 rounded-xl">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="w-6 h-6 rounded bg-brand/20 text-brand flex items-center justify-center text-xs">IF</span>
              Condition
            </h3>
            
            <div className="grid grid-cols-3 gap-2">
              <select value={metric} onChange={e => setMetric(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-sm text-white focus:outline-none focus:border-brand">
                <option value="soil_moisture">Soil Moisture</option>
                <option value="battery_pct">Battery %</option>
                <option value="temperature">Temperature</option>
              </select>
              
              <select value={operator} onChange={e => setOperator(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-sm text-white focus:outline-none focus:border-brand">
                <option value="<">is less than</option>
                <option value=">">is greater than</option>
                <option value="==">is exactly</option>
              </select>
              
              <input 
                type="number" 
                value={value} 
                onChange={e => setValue(e.target.value)}
                placeholder="Value" 
                className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand"
              />
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowRight className="w-5 h-5 rotate-90" />
          </div>

          <div className="space-y-3 bg-white/3 border border-white/5 p-4 rounded-xl">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="w-6 h-6 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs">THEN</span>
              Action
            </h3>
            
            <div className="grid grid-cols-2 gap-2">
              <select value={actionType} onChange={e => setActionType(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-sm text-white focus:outline-none focus:border-brand">
                <option value="create_alert">Create Alert</option>
                <option value="notify">Send Notification</option>
              </select>
              
              {actionType === 'create_alert' && (
                <select value={severity} onChange={e => setSeverity(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-sm text-white focus:outline-none focus:border-brand">
                  <option value="INFO">Info</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-white/5 flex justify-end gap-3 bg-white/[0.02]">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button 
            onClick={() => create.mutate()} 
            disabled={create.isPending || !name || !value}
            className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {create.isPending ? 'Saving...' : 'Save Rule'}
          </button>
        </div>
      </div>
    </div>
  )
}
