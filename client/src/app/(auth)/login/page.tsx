'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { motion } from 'framer-motion'
import { useToast } from '@/components/ui/use-toast'
import { Loader2, Mail, Lock } from 'lucide-react'
import Link from 'next/link'
import { Container, Grid, Paper, TextField, Button, Typography, Chip, Box, InputAdornment } from '@mui/material'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(email, password)
      toast({
        title: 'Welcome back! 👋',
        description: 'Redirecting to dashboard...',
      })
      router.push('/dashboard')
    } catch (error: any) {
      toast({
        title: 'Login failed',
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
              <Box sx={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(34,211,238,0.08), transparent 40%, rgba(37,99,235,0.08))' }} />
              <Box sx={{ position: 'relative' }}>
                <Chip label="Secure multi-agent orchestration" size="small" sx={{ borderColor: 'rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', color: 'text.secondary', mb: 2 }} variant="outlined" />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>Welcome back.</Typography>
                <Typography variant="body1" sx={{ color: 'text.secondary', maxWidth: 640, mb: 3 }}>
                  Sign in to launch parallel runs, compare answers, and keep your prompts organized with saved presets.
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', px: 2, py: 1.5 }}>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>Realtime</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>Sub-1s fan-out</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.7)', px: 2, py: 1.5 }}>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>Comparison</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>Side-by-side diffs</Typography>
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
                  <Box sx={{ width: 40, height: 40, borderRadius: 2, background: 'linear-gradient(135deg,#22d3ee,#2563eb)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>⚡</Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>Sign in to</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>Multi-AI Orchestrator</Typography>
                  </Box>
                </Box>
                <Chip label="Live" size="small" color="success" variant="outlined" sx={{ bgcolor: 'rgba(16,185,129,0.12)', color: 'rgb(110,231,183)', borderColor: 'rgba(16,185,129,0.3)' }} />
              </Box>

              <Box component="form" onSubmit={handleSubmit} sx={{ display: 'grid', gap: 2 }}>
                <TextField
                  label="Email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  InputProps={{ startAdornment: <InputAdornment position="start"><Mail size={18} color="#64748b" /></InputAdornment> }}
                  sx={{
                    '& .MuiOutlinedInput-root': { bgcolor: 'rgba(2,6,23,0.8)' },
                  }}
                />
                <TextField
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  InputProps={{ startAdornment: <InputAdornment position="start"><Lock size={18} color="#64748b" /></InputAdornment> }}
                  sx={{
                    '& .MuiOutlinedInput-root': { bgcolor: 'rgba(2,6,23,0.8)' },
                  }}
                />
                <Button type="submit" disabled={loading} variant="contained" color="primary" sx={{ py: 1.2, fontWeight: 600 }}>
                  {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </Box>

              <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', mt: 2 }}>
                Don't have an account?{' '}
                <Link href="/register" className="text-cyan-300 hover:text-cyan-200 font-semibold">Sign up</Link>
              </Typography>

              <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderRadius: 3, border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.6)', px: 2, py: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>SSO coming soon</Typography>
                <Typography variant="caption" sx={{ color: 'rgb(110,231,183)' }}>Secure & private</Typography>
              </Box>
            </Paper>
          </motion.div>
        </Grid>
      </Grid>
    </Container>
  )
}
