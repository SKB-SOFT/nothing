"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Loader2, Send, Trash2, Sparkles, Keyboard, Timer, ShieldCheck } from "lucide-react"
import { Paper, TextField, Button, Typography, Chip, Box, Grid } from "@mui/material"

const AGENTS = [
  { id: "hf-gptj", name: "GPT-J", badge: "Fast", color: "from-cyan-500/30 to-blue-600/20" },
  { id: "hf-falcon", name: "Falcon 7B", badge: "Balanced", color: "from-amber-400/30 to-orange-500/20" },
  { id: "hf-llama", name: "LLaMA 2", badge: "Deep", color: "from-fuchsia-500/25 to-pink-500/20" },
]

export function QueryInput({ onSubmit, loading }: { onSubmit: (text: string, agents: string[]) => void; loading: boolean }) {
  const [query, setQuery] = useState("")
  const [selectedAgents, setSelectedAgents] = useState(["hf-gptj", "hf-falcon"])

  const handleToggleAgent = (agentId: string) => {
    setSelectedAgents((prev) => (prev.includes(agentId) ? prev.filter((id) => id !== agentId) : [...prev, agentId]))
  }

  const handleSubmit = () => {
    if (query.trim() && selectedAgents.length > 0) {
      onSubmit(query, selectedAgents)
      setQuery("")
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'grid', gap: 16 }}>
      <Paper elevation={0} sx={{ bgcolor: 'rgba(1,4,14,0.85)', border: '1px solid rgba(30,41,59,0.8)', p: 3, borderRadius: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>Composer</Typography>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>Ask multiple agents in parallel</Typography>
            </Box>
            <Chip icon={<Keyboard size={14} />} label="Cmd/Ctrl + Enter" size="small" variant="outlined" sx={{ borderColor: 'rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.6)', color: 'text.secondary' }} />
          </Box>

          <Box sx={{ position: 'relative' }}>
            <Box sx={{ position: 'absolute', inset: 0, borderRadius: 2, background: 'linear-gradient(90deg, rgba(34,211,238,0.08), transparent 50%, rgba(251,191,36,0.08))', filter: 'blur(6px)' }} />
            <Box sx={{ position: 'relative', borderRadius: 2, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.8)', p: 1.5 }}>
              <Sparkles size={18} color="#fde68a" style={{ position: 'absolute', left: 16, top: 16 }} />
              <TextField
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask any question... e.g., Compare GPT-J and LLaMA 2 on summarizing this article"
                multiline
                minRows={2}
                maxRows={6}
                inputProps={{ maxLength: 5000 }}
                fullWidth
                sx={{
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'transparent',
                    pl: 4,
                  },
                }}
              />
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" sx={{ display: 'inline-flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
              <Timer size={14} /> ~1s fan-out <ShieldCheck size={14} /> Guardrails on
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>{query.length} / 5000</Typography>
          </Box>
        </Box>

        <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid rgba(30,41,59,0.8)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>Select AI Models</Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>Choose 1-3</Typography>
          </Box>
          <Grid container spacing={1.5}>
            {AGENTS.map((agent) => {
              const active = selectedAgents.includes(agent.id)
              return (
                <Grid item xs={12} md={4} key={agent.id}>
                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                    <Paper
                      onClick={() => handleToggleAgent(agent.id)}
                      elevation={0}
                      sx={{
                        position: 'relative', overflow: 'hidden', borderRadius: 2, px: 2, py: 1.5, cursor: 'pointer',
                        border: active ? '1px solid rgba(34,211,238,0.6)' : '1px solid rgba(30,41,59,0.8)',
                        boxShadow: active ? '0 10px 40px -30px rgba(34,211,238,0.6)' : 'none',
                        bgcolor: 'rgba(2,6,23,0.7)',
                      }}
                    >
                      {active && <Box sx={{ position: 'absolute', inset: 0, background: `linear-gradient(135deg, ${agent.color.replace('from-', '').replace(' to-', ' , ')})`, opacity: 0.7 }} />}
                      <Box sx={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>{agent.name}</Typography>
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>{agent.badge}</Typography>
                        </Box>
                        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: active ? 'rgb(16,185,129)' : 'rgb(71,85,105)', boxShadow: active ? '0 0 0 6px rgba(16,185,129,0.2)' : 'none' }} />
                      </Box>
                    </Paper>
                  </motion.div>
                </Grid>
              )
            })}
          </Grid>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, pt: 1 }}>
            {["Summarize", "Compare", "Explain", "Pros & Cons"].map((chip) => (
              <Chip
                key={chip}
                label={chip}
                size="small"
                onClick={() => setQuery((q) => (q ? q + `\n\n${chip}: ` : `${chip}: `))}
                variant="outlined"
                sx={{ borderColor: 'rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', color: 'text.secondary' }}
              />
            ))}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, mt: 3, pt: 3, borderTop: '1px solid rgba(30,41,59,0.8)', alignItems: 'center' }}>
          <motion.div style={{ flex: 1 }} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
            <Button
              onClick={handleSubmit}
              disabled={loading || !query.trim() || selectedAgents.length === 0}
              variant="contained"
              color="primary"
              fullWidth
              sx={{ py: 1.2, fontWeight: 600 }}
            >
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {loading ? "Processing..." : "Send Query"}
              <Send className="w-4 h-4 ml-2" />
            </Button>
          </motion.div>

          <Button
            onClick={() => {
              setQuery("")
              setSelectedAgents(["hf-gptj", "hf-falcon"])
            }}
            variant="outlined"
            color="inherit"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </Box>
      </Paper>

      <Typography variant="caption" sx={{ color: 'text.secondary', textAlign: 'center' }}>
        Tip: Press <Box component="span" sx={{ bgcolor: 'rgba(2,6,23,0.8)', px: 1, py: 0.5, borderRadius: 1, border: '1px solid rgba(51,65,85,0.7)', color: 'text.primary' }}>Cmd/Ctrl</Box> + <Box component="span" sx={{ bgcolor: 'rgba(2,6,23,0.8)', px: 1, py: 0.5, borderRadius: 1, border: '1px solid rgba(51,65,85,0.7)', color: 'text.primary' }}>Enter</Box> to submit
      </Typography>
    </motion.div>
  )
}
