"use client"

import React, { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Moon, Sun } from "lucide-react"

export function ThemeToggle() {
  const [dark, setDark] = useState(true)

  useEffect(() => {
    const root = document.documentElement
    if (dark) root.classList.add("dark")
    else root.classList.remove("dark")
  }, [dark])

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => setDark((v) => !v)}
      className="border-slate-800 text-slate-100 hover:bg-slate-900"
      aria-label="Toggle theme"
      title="Toggle theme"
    >
      {dark ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
    </Button>
  )
}
