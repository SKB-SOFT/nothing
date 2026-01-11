'use client'

import React from 'react'
import { useToast } from './use-toast'

export function Toaster() {
  const { toasts, dismiss } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`w-72 rounded-lg border px-4 py-3 shadow-xl backdrop-blur bg-slate-900/80 border-slate-700 text-slate-100 transition transform hover:-translate-y-0.5 ${toast.variant === 'destructive' ? 'border-red-500/60 bg-red-900/60 text-red-50' : ''}`}
        >
          <div className="flex justify-between items-start gap-2">
            <div>
              {toast.title && <p className="font-semibold text-sm">{toast.title}</p>}
              {toast.description && <p className="text-xs text-slate-300 mt-1">{toast.description}</p>}
            </div>
            <button
              onClick={() => dismiss(toast.id)}
              aria-label="Dismiss toast"
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
