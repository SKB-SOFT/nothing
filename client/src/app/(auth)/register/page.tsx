'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { motion } from 'framer-motion'
import { useToast } from '@/components/ui/use-toast'
import { Loader2, Mail, Lock, User } from 'lucide-react'
import Link from 'next/link'
import { Container, Grid, Paper, TextField, Button, Typography, Chip, Box, InputAdornment } from '@mui/material'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const router = useRouter()
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await register(email, password, fullName)
      toast({
        title: 'Account created! 🎉',
        description: 'Redirecting to dashboard...',
      })
      router.push('/dashboard')
    } catch (error: any) {
      toast({
        title: 'Registration failed',
        description: error.message,
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="lg" sx={{ minHeight: '100vh', px: 3, py: 6, display: 'flex', alignItems: 'center' }}>
      <Grid container spacing={4} alignItems="center">
        <Grid item xs={12} lg={7}>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
            <Paper elevation={0} sx={{ position: 'relative', overflow: 'hidden', borderRadius: 4, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', backdropFilter: 'blur(6px)', p: 4 }}>
              <Box sx={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(251,191,36,0.1), transparent 40%, rgba(236,72,153,0.1))' }} />
              <Box sx={{ position: 'relative' }}>
                <Chip label="Start orchestrating in minutes" size="small" sx={{ borderColor: 'rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', color: 'text.secondary', mb: 2 }} variant="outlined" />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>Create your workspace.</Typography>
                <Typography variant="body1" sx={{ color: 'text.secondary', maxWidth: 640, mb: 3 }}>
                  Spin up parallel agents, capture responses, and keep your team aligned with consistent prompts and safety rails.
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', px: 2, py: 1.5 }}>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>Collaboration</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>Shareable runs</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', px: 2, py: 1.5 }}>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>Controls</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>Rate limits & guardrails</Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            </Paper>
          </motion.div>
        </Grid>

        <Grid item xs={12} lg={5}>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, delay: 0.1 }}>
            <Paper elevation={0} sx={{ borderRadius: 4, bgcolor: 'rgba(1,4,14,0.8)', border: '1px solid rgba(30,41,59,0.8)', backdropFilter: 'blur(8px)', p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box sx={{ width: 40, height: 40, borderRadius: 2, background: 'linear-gradient(135deg,#f59e0b,#ec4899)', color: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>✦</Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>Create your account</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>Multi-AI Orchestrator</Typography>
                  </Box>
                </Box>
                <Chip label="Free tier" size="small" variant="outlined" sx={{ bgcolor: 'rgba(6,182,212,0.12)', color: 'rgb(165,243,252)', borderColor: 'rgba(6,182,212,0.3)' }} />
              </Box>

              <Box component="form" onSubmit={handleSubmit} sx={{ display: 'grid', gap: 2 }}>
                <TextField
                  label="Full Name"
                  type="text"
                  placeholder="Alex Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  InputProps={{ startAdornment: <InputAdornment position="start"><User size={18} color="#64748b" /></InputAdornment> }}
                  sx={{ '& .MuiOutlinedInput-root': { bgcolor: 'rgba(2,6,23,0.8)' } }}
                />
                <TextField
                  label="Email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  InputProps={{ startAdornment: <InputAdornment position="start"><Mail size={18} color="#64748b" /></InputAdornment> }}
                  sx={{ '& .MuiOutlinedInput-root': { bgcolor: 'rgba(2,6,23,0.8)' } }}
                />
                <TextField
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  InputProps={{ startAdornment: <InputAdornment position="start"><Lock size={18} color="#64748b" /></InputAdornment> }}
                  sx={{ '& .MuiOutlinedInput-root': { bgcolor: 'rgba(2,6,23,0.8)' } }}
                />
                <Button type="submit" disabled={loading} variant="contained" color="primary" sx={{ py: 1.2, fontWeight: 600 }}>
                  {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  {loading ? 'Creating account...' : 'Create Account'}
                </Button>
              </Box>

              <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', mt: 2 }}>
                Already have an account?{' '}
                <Link href="/login" className="text-cyan-300 hover:text-cyan-200 font-semibold">Sign in</Link>
              </Typography>

              <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderRadius: 3, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.6)', px: 2, py: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>Ships with audit logs</Typography>
                <Typography variant="caption" sx={{ color: 'rgb(253,186,116)' }}>SOC2-ready patterns</Typography>
              </Box>
            </Paper>
          </motion.div>
        </Grid>
      </Grid>
    </Container>
  )
}
