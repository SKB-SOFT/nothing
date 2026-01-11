'use client'

import { motion } from 'framer-motion'
import { Copy, Download, Share2, Zap, CheckCircle, Clock3, Database } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { Paper, Box, Typography, Button, Chip } from '@mui/material'

export function ResponseCard({ response, index }: { response: any; index: number }) {
  const { toast } = useToast()

  const handleCopy = () => {
    navigator.clipboard.writeText(response.response_text)
    toast({
      title: 'Copied!',
      description: 'Response copied to clipboard',
    })
  }

  const handleDownload = () => {
    const element = document.createElement('a')
    element.setAttribute('href', `data:text/plain;charset=utf-8,${encodeURIComponent(response.response_text)}`)
    element.setAttribute('download', `${response.agent_id}-response.txt`)
    element.click()
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      whileHover={{ y: -4 }}
      style={{ height: '100%' }}
    >
      <Paper elevation={0} sx={{ height: '100%', overflow: 'hidden', border: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(1,4,14,0.85)', boxShadow: '0 18px 70px -50px rgba(0,0,0,0.8)', borderRadius: 3 }}>
        <Box sx={{ position: 'relative', height: 4, width: '100%', background: 'linear-gradient(90deg,#22d3ee,#f59e0b,#ec4899)' }} />

        {/* Header */}
        <Box sx={{ p: 2, borderBottom: '1px solid rgba(30,41,59,0.8)', bgcolor: 'rgba(2,6,23,0.6)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box sx={{ width: 40, height: 40, borderRadius: 2, background: 'linear-gradient(135deg,#22d3ee,#2563eb)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Zap size={20} color="#fff" />
              </Box>
              <Box sx={{ lineHeight: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>{response.agent_name}</Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>{response.model_info?.type || 'Transformer'}</Typography>
              </Box>
            </Box>
            {response.status === 'success' && (
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity }}>
                <CheckCircle size={20} color="rgb(52,211,153)" />
              </motion.div>
            )}
          </Box>
        </Box>

        {/* Content */}
        <Box sx={{ p: 2, display: 'grid', gap: 1.5, maxHeight: 320, overflowY: 'auto' }}>
          {response.response_text && (
            <Typography variant="body2" sx={{ color: 'text.primary', lineHeight: 1.6 }}>
              {response.response_text.slice(0, 800)}
              {response.response_text.length > 800 && (
                <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary', mt: 0.5 }}>… truncated for preview</Typography>
              )}
            </Typography>
          )}

          {response.status === 'error' && (
            <Box sx={{ bgcolor: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 2, p: 1.5 }}>
              <Typography variant="body2" sx={{ color: 'rgb(252,165,165)' }}>{response.error_message || 'Request failed'}</Typography>
            </Box>
          )}
        </Box>

        {/* Metadata */}
        <Box sx={{ px: 2, pb: 1.5, display: 'grid', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, color: 'text.secondary' }}>
              <Clock3 size={14} /> Response time
            </Typography>
            <Typography variant="caption" sx={{ fontFamily: 'JetBrains Mono, monospace' }}>{response.response_time_ms.toFixed(0)}ms</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, color: 'text.secondary' }}>
              <Database size={14} /> Tokens
            </Typography>
            <Typography variant="caption" sx={{ fontFamily: 'JetBrains Mono, monospace' }}>{response.token_count}</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip label={response.status === 'success' ? 'Success' : 'Result'} size="small" variant="outlined" sx={{ bgcolor: 'rgba(2,6,23,0.7)', borderColor: 'rgba(30,41,59,0.8)', color: 'text.secondary' }} />
            {response.cached && (
              <Chip label="Cached" size="small" variant="outlined" sx={{ bgcolor: 'rgba(16,185,129,0.12)', borderColor: 'rgba(16,185,129,0.4)', color: 'rgb(110,231,183)' }} />
            )}
          </Box>
        </Box>

        {/* Actions */}
        <Box sx={{ borderTop: '1px solid rgba(30,41,59,0.8)', p: 2, display: 'flex', gap: 1 }}>
          <Button onClick={handleCopy} variant="text" color="inherit" sx={{ flex: 1 }}>
            <Copy className="w-4 h-4 mr-1" /> Copy
          </Button>
          <Button onClick={handleDownload} variant="text" color="inherit" sx={{ flex: 1 }}>
            <Download className="w-4 h-4 mr-1" /> Download
          </Button>
          <Button variant="text" color="inherit" sx={{ flex: 1 }}>
            <Share2 className="w-4 h-4 mr-1" /> Share
          </Button>
        </Box>
      </Paper>
    </motion.div>
  )
}
