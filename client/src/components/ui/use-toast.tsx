'use client'

import React, { createContext, useCallback, useContext, useMemo, useState } from 'react'

export type ToastVariant = 'default' | 'destructive'

export type Toast = {
  id: number
  title?: string
  description?: string
  variant?: ToastVariant
}

interface ToastContextValue {
  toasts: Toast[]
  toast: (toast: Omit<Toast, 'id'>) => void
  dismiss: (id: number) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const toast = useCallback(
    (toastInput: Omit<Toast, 'id'>) => {
      const id = Date.now()
      const nextToast: Toast = { id, ...toastInput }
      setToasts((prev) => [...prev, nextToast])
      // Auto-dismiss after 4 seconds
      setTimeout(() => dismiss(id), 4000)
    },
    [dismiss]
  )

  const value = useMemo(() => ({ toasts, toast, dismiss }), [toasts, toast, dismiss])

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}
