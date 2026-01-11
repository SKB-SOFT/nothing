"use client"

import React, { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, ArrowRight, Sparkles, Zap } from "lucide-react"

const COMMANDS = [
  { label: "Go to Dashboard", action: "dashboard", hint: "Open main workspace" },
  { label: "New Query", action: "new-query", hint: "Start a fresh multi-model run" },
  { label: "Login", action: "login", hint: "Sign in to your account" },
  { label: "Register", action: "register", hint: "Create a new account" },
]

export function CommandPalette() {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [term, setTerm] = useState("")

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().includes("MAC")
      if ((isMac && e.metaKey && e.key.toLowerCase() === "k") || (!isMac && e.ctrlKey && e.key.toLowerCase() === "k")) {
        e.preventDefault()
        setOpen(true)
      }
      if (e.key === "Escape") setOpen(false)
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])

  const filtered = useMemo(() => {
    const t = term.trim().toLowerCase()
    if (!t) return COMMANDS
    return COMMANDS.filter(c => c.label.toLowerCase().includes(t) || c.hint.toLowerCase().includes(t))
  }, [term])

  const run = (action: string) => {
    setOpen(false)
    switch (action) {
      case "dashboard":
        router.push("/dashboard"); break
      case "new-query":
        router.push("/dashboard"); break
      case "login":
        router.push("/login"); break
      case "register":
        router.push("/register"); break
      default:
        break
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-lg bg-slate-950/80 border border-slate-800/80">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-amber-400 flex items-center justify-center">
            <Zap className="w-4 h-4 text-slate-900" />
          </div>
          <div>
            <p className="text-sm text-slate-400">Command Palette</p>
            <p className="text-xs text-slate-500">Press Esc to close</p>
          </div>
        </div>
        <div className="relative mb-4">
          <Search className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
          <Input
            autoFocus
            placeholder="Type a command..."
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            className="pl-10 bg-slate-900 border-slate-800 text-slate-100"
          />
        </div>
        <div className="space-y-2">
          {filtered.map(cmd => (
            <button
              key={cmd.action}
              onClick={() => run(cmd.action)}
              className="w-full text-left rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 hover:border-cyan-500/40 hover:bg-slate-900 transition flex items-center justify-between"
            >
              <div>
                <p className="text-sm text-slate-100">{cmd.label}</p>
                <p className="text-xs text-slate-500">{cmd.hint}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500" />
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="text-xs text-slate-500 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5" /> Try: Dashboard, Login
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
