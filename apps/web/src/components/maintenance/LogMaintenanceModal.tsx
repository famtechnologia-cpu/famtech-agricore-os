'use client'
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { maintenanceApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'
import { X, Save } from 'lucide-react'

export default function LogMaintenanceModal({ onClose }: { onClose: () => void }) {
  const currentFarm = useStore(s => s.currentFarm)
  const qc = useQueryClient()

  const [type, setType] = useState('INSPECTION')
  const [description, setDescription] = useState('')
  const [cost, setCost] = useState('')
  const [notes, setNotes] = useState('')

  const create = useMutation({
    mutationFn: async () => {
      if (!currentFarm) throw new Error('No farm selected')
      await maintenanceApi.log(currentFarm.id, {
        device_id: 'manual', // In a real app, you'd select a device from a dropdown
        type,
        description,
        cost: cost ? parseFloat(cost) : undefined,
        notes,
        performed_at: new Date().toISOString(),
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['maintenance', currentFarm?.id] })
      onClose()
    }
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0a0c10] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-slide-up">
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <h2 className="text-lg font-display font-bold text-white">Log Maintenance</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">Type</label>
            <select 
              value={type} 
              onChange={e => setType(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand"
            >
              <option value="INSPECTION">Inspection</option>
              <option value="CLEANING">Cleaning</option>
              <option value="CALIBRATION">Calibration</option>
              <option value="REPAIR">Repair</option>
              <option value="REPLACEMENT">Replacement</option>
              <option value="FIRMWARE_UPDATE">Firmware Update</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">Description</label>
            <input 
              type="text" 
              value={description} 
              onChange={e => setDescription(e.target.value)}
              placeholder="e.g. Replaced battery pack" 
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">Cost ($) (Optional)</label>
            <input 
              type="number" 
              value={cost} 
              onChange={e => setCost(e.target.value)}
              placeholder="0.00" 
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">Notes (Optional)</label>
            <textarea 
              value={notes} 
              onChange={e => setNotes(e.target.value)}
              placeholder="Any additional details..." 
              rows={3}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand resize-none"
            />
          </div>
        </div>

        <div className="p-4 border-t border-white/5 flex justify-end gap-3 bg-white/[0.02]">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button 
            onClick={() => create.mutate()} 
            disabled={create.isPending || !description}
            className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {create.isPending ? 'Saving...' : 'Log Event'}
          </button>
        </div>
      </div>
    </div>
  )
}
