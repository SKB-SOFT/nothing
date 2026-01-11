'use client'

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { useAuth } from "@/context/AuthContext"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Zap, ArrowRight, Sparkles, ShieldCheck, Cpu } from "lucide-react"

export default function Home() {
  const router = useRouter()
  const { user } = useAuth()

  useEffect(() => {
    if (user) {
      router.push("/dashboard")
    }
  }, [user, router])

  const preview = [
    { title: "GPT-J • Fast", body: "Summarized the report in 2 sentences with action items.", accent: "from-cyan-400 to-blue-500", latency: "420ms" },
    { title: "Falcon 7B • Balanced", body: "Offered a structured comparison with pros/cons.", accent: "from-amber-400 to-orange-500", latency: "690ms" },
    { title: "LLaMA 2 • Deep", body: "Provided citations and risk flags for deployment.", accent: "from-fuchsia-500 to-pink-500", latency: "980ms" },
  ]

  return (
    <div className="relative min-h-screen flex items-center justify-center px-6 py-16">
      <div className="max-w-6xl w-full grid gap-12 lg:grid-cols-2 items-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="space-y-8"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-700/60 bg-slate-900/70 px-4 py-2 text-sm text-slate-200 shadow-lg shadow-cyan-500/10">
            <span className="relative inline-flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75 animate-ping" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-400" />
            </span>
            New • Multi-model orchestrator
          </div>

          <div className="space-y-4">
            <h1 className="text-5xl md:text-6xl font-bold leading-tight">
              Orchestrate models.
              <br />
              Compare answers instantly.
            </h1>
            <p className="text-lg text-slate-300 max-w-2xl">
              Launch parallel queries to multiple LLMs, view diffs side-by-side, and pick the best insight without waiting.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <Button
              onClick={() => router.push("/dashboard")}
              size="lg"
              className="bg-gradient-to-r from-cyan-500 to-amber-400 hover:from-cyan-400 hover:to-amber-300 text-slate-900 font-semibold shadow-lg shadow-cyan-500/30"
            >
              Launch orchestrator
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button
              onClick={() => router.push("/register")}
              size="lg"
              variant="outline"
              className="border-slate-700 bg-slate-900/60 text-slate-100 hover:bg-slate-800"
            >
              Create account
            </Button>
          </div>

          <div className="grid sm:grid-cols-3 gap-3 text-sm">
            <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2">
              <Cpu className="w-4 h-4 text-cyan-300" />
              <span className="text-slate-300">Parallel agents</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2">
              <ShieldCheck className="w-4 h-4 text-emerald-300" />
              <span className="text-slate-300">Safety guardrails</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2">
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span className="text-slate-300">Smart prompts</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.15 }}
          className="relative"
        >
          <div className="absolute -inset-6 bg-gradient-to-br from-cyan-500/15 via-transparent to-amber-400/10 blur-3xl" />
          <div className="relative rounded-2xl border border-slate-800/80 bg-slate-900/70 backdrop-blur shadow-[0_30px_120px_-50px_rgba(0,0,0,0.8)] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-white" />
                </div>
                Multi-model run
              </div>
              <div className="text-xs text-slate-400">Live preview</div>
            </div>

            <div className="grid gap-3">
              {preview.map((card, idx) => (
                <motion.div
                  key={card.title}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + idx * 0.08 }}
                  className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow-lg shadow-black/30"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-slate-100">
                      <span className={`inline-flex h-6 items-center rounded-full bg-gradient-to-r ${card.accent} px-2 text-xs font-semibold text-slate-900`}>{card.title}</span>
                    </div>
                    <span className="text-xs text-slate-400">{card.latency}</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">{card.body}</p>
                </motion.div>
              ))}
            </div>

            <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3 text-sm text-slate-200">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-300" />
                Auto-pick the strongest answer
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
