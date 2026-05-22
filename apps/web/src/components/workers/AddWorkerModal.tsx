'use client'
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useStore } from '@/lib/store/useStore'
import { X, Save } from 'lucide-react'
import axios from '@/lib/api/client'

export default function AddWorkerModal({ onClose }: { onClose: () => void }) {
  const currentFarm = useStore(s => s.currentFarm)
  const qc = useQueryClient()

  const [name, setName] = useState('')
  const [role, setRole] = useState('Harvester')
  const [phone, setPhone] = useState('')

  const create = useMutation({
    mutationFn: async () => {
      if (!currentFarm) throw new Error('No farm selected')
      await axios.post(`/farms/${currentFarm.id}/workers`, {
        name,
        role,
        phone,
        active: true,
        on_site: false,
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workers', currentFarm?.id] })
      onClose()
    }
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0a0c10] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-slide-up">
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <h2 className="text-lg font-display font-bold text-white">Add New Worker</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">Full Name</label>
            <input 
              type="text" 
              value={name} 
              onChange={e => setName(e.target.value)}
              placeholder="Jane Doe" 
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">Role</label>
            <select 
              value={role} 
              onChange={e => setRole(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand"
            >
              <option value="Farm Manager">Farm Manager</option>
              <option value="Harvester">Harvester</option>
              <option value="Technician">Technician</option>
              <option value="Security">Security</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">Phone (Optional)</label>
            <input 
              type="tel" 
              value={phone} 
              onChange={e => setPhone(e.target.value)}
              placeholder="+1 555-0192" 
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand"
            />
          </div>
        </div>

        <div className="p-4 border-t border-white/5 flex justify-end gap-3 bg-white/[0.02]">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button 
            onClick={() => create.mutate()} 
            disabled={create.isPending || !name}
            className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {create.isPending ? 'Saving...' : 'Add Worker'}
          </button>
        </div>
      </div>
    </div>
  )
}
