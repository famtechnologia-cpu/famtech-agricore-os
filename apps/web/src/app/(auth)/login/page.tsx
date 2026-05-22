'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi, farmApi } from '@/lib/api/client'
import { useStore } from '@/lib/store/useStore'

export default function LoginPage() {
  const router = useRouter()
  const { setUser, setFarms, setCurrentFarm } = useStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await authApi.login(email, password)
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      const me = await authApi.me()
      setUser(me.data)
      const farms = await farmApi.list()
      const farmList = farms.data
      setFarms(farmList)
      if (farmList.length > 0) setCurrentFarm(farmList[0])
      router.push('/dashboard')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Login failed. Check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#08090c] px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-display font-bold text-white">
            Famtech <span className="text-brand">AgriCore</span>
          </h1>
          <p className="text-slate-400 text-sm mt-2">Farm Operating System</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase tracking-wider">Email</label>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand/50 text-sm"
              placeholder="you@farm.com"
            />
          </div>
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase tracking-wider">Password</label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand/50 text-sm"
              placeholder="••••••••"
            />
          </div>
          {error && (
            <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>
          )}
          <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 text-sm font-semibold disabled:opacity-60">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-xs text-slate-500 mt-6 font-mono">
          AgriCore OS · Famtech © 2026
        </p>
      </div>
    </div>
  )
}
