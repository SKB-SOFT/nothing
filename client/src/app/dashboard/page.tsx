'use client'

import { useAuth } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { QueryInput } from '@/components/dashboard/QueryInput'
import { ResponseCard } from '@/components/dashboard/ResponseCard'
import { QueryHistory } from '@/components/dashboard/QueryHistory'
import { useToast } from '@/components/ui/use-toast'
import { queryAPI } from '@/lib/api'
import { Container, Grid, Paper, Typography, Chip, Box } from '@mui/material'

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const { toast } = useToast()
  const [responses, setResponses] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [currentQuery, setCurrentQuery] = useState('')

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  const handleSubmitQuery = async (queryText: string, selectedAgents: string[]) => {
    setLoading(true)
    setCurrentQuery(queryText)
    try {
      const response = await queryAPI.submit(queryText, selectedAgents)
      setResponses(response.data.responses)
      toast({
        title: 'Query submitted successfully! 🎉',
        description: `Got responses from ${response.data.responses.length} models`,
      })
    } catch (error: any) {
      toast({
        title: 'Error submitting query',
        description: error.response?.data?.detail || 'Something went wrong',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  if (authLoading) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Loader2 className="w-8 h-8 animate-spin" color="#22d3ee" />
      </Box>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ minHeight: '100vh', py: 6 }}>
      <Box sx={{ display: 'grid', gap: 5 }}>
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }}>
          <Box sx={{ display: 'grid', gap: 2 }}>
            <Chip label="Live runspace" size="small" variant="outlined" sx={{ width: 'fit-content', borderColor: 'rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', color: 'text.secondary' }} />
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
                Welcome back, <Box component="span" sx={{ background: 'linear-gradient(90deg,#22d3ee,#f59e0b)', WebkitBackgroundClip: 'text', color: 'transparent' }}>{user?.full_name}</Box>
              </Typography>
              <Typography variant="body1" sx={{ color: 'text.secondary', mt: 1.5, maxWidth: 640 }}>
                Orchestrate multiple LLMs in parallel, compare answers instantly, and keep your best prompts close.
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {['Cache-aware', 'Latency tracking', 'Diff-friendly outputs'].map((pill) => (
                <Chip key={pill} label={pill} size="small" variant="outlined" sx={{ borderColor: 'rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', color: 'text.secondary' }} />
              ))}
            </Box>
          </Box>
        </motion.div>

        {/* Stats */}
        <Grid container spacing={2}>
          {[{
            label: 'Daily quota',
            value: `${user?.quota_daily || 50} queries`,
            gradient: 'linear-gradient(135deg, rgba(34,211,238,0.25), rgba(37,99,235,0.18))',
          }, {
            label: 'Status',
            value: 'Active',
            gradient: 'linear-gradient(135deg, rgba(16,185,129,0.25), rgba(45,212,191,0.18))',
          }, {
            label: 'Models available',
            value: '3 models',
            gradient: 'linear-gradient(135deg, rgba(251,191,36,0.25), rgba(236,72,153,0.18))',
          }].map((card, idx) => (
            <Grid item xs={12} md={4} key={card.label}>
              <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 * (idx + 1) }}>
                <Paper elevation={0} sx={{ position: 'relative', overflow: 'hidden', borderRadius: 3, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(1,4,14,0.85)', p: 3, boxShadow: '0 18px 60px -40px rgba(0,0,0,0.8)' }}>
                  <Box sx={{ position: 'absolute', inset: 0, background: card.gradient, opacity: 0.8 }} />
                  <Box sx={{ position: 'relative', display: 'grid', gap: 0.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>{card.label}</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>{card.value}</Typography>
                  </Box>
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        {/* Main Content */}
        <Grid container spacing={2}>
          <Grid item xs={12} lg={8}>
            <motion.div initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }}>
              <QueryInput onSubmit={handleSubmitQuery} loading={loading} />
            </motion.div>
          </Grid>
          <Grid item xs={12} lg={4}>
            <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }}>
              <QueryHistory />
            </motion.div>
          </Grid>
        </Grid>

        {/* Responses */}
        {responses.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>Responses</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>{responses.length} models returned</Typography>
            </Box>
            <Grid container spacing={2}>
              {responses.map((response, index) => (
                <Grid item xs={12} md={6} lg={4} key={response.agent_id}>
                  <ResponseCard response={response} index={index} />
                </Grid>
              ))}
            </Grid>
          </motion.div>
        )}
      </Box>
    </Container>
  )
}
