'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useStore } from '@/lib/store/useStore'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

export function Providers({ children }: { children: React.ReactNode }) {
  const setOnline = useStore((s) => s.setOnline)

  useEffect(() => {
    const handler = () => setOnline(navigator.onLine)
    window.addEventListener('online', handler)
    window.addEventListener('offline', handler)
    return () => { window.removeEventListener('online', handler); window.removeEventListener('offline', handler) }
  }, [setOnline])

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
