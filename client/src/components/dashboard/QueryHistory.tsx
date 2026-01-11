'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2, Clock, Trash2, Search } from 'lucide-react'
import { queryAPI } from '@/lib/api'
import { Paper, TextField, Typography, Box, IconButton } from '@mui/material'

export function QueryHistory() {
  const [queries, setQueries] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchQueries()
  }, [])

  const fetchQueries = async () => {
    try {
      setLoading(true)
      const response = await queryAPI.getHistory(20, 0)
      setQueries(response.data.queries)
    } catch (error) {
      console.error('Error fetching queries:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredQueries = queries.filter((q) =>
    q.query_text.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
      <Paper elevation={0} sx={{ bgcolor: 'rgba(1,4,14,0.85)', border: '1px solid rgba(30,41,59,0.8)', p: 3, borderRadius: 3, boxShadow: '0 18px 60px -50px rgba(0,0,0,0.8)' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="body1" sx={{ fontWeight: 600 }}>Query History</Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>Last 20</Typography>
        </Box>

        <Box sx={{ position: 'relative', mb: 2 }}>
          <Search style={{ position: 'absolute', left: 12, top: 12 }} size={16} color="#64748b" />
          <TextField
            placeholder="Search queries..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            fullWidth
            sx={{ '& .MuiOutlinedInput-root': { pl: 3, bgcolor: 'rgba(2,6,23,0.8)' } }}
          />
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
            <Loader2 className="w-5 h-5 animate-spin" color="#22d3ee" />
          </Box>
        ) : filteredQueries.length === 0 ? (
          <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', py: 4 }}>No queries yet</Typography>
        ) : (
          <Box sx={{ display: 'grid', gap: 1.5, maxHeight: 384, overflowY: 'auto', pr: 0.5 }}>
            {filteredQueries.map((query, idx) => (
              <motion.div key={query.query_id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.05 }}>
                <Box sx={{ p: 1.5, bgcolor: 'rgba(2,6,23,0.6)', border: '1px solid rgba(30,41,59,0.8)', borderRadius: 2, ':hover': { borderColor: 'rgba(34,211,238,0.4)' }, cursor: 'pointer' }}>
                  <Box sx={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', gap: 1 }}>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="body2" sx={{ color: 'text.primary', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: 500 }}>
                        {query.query_text}
                      </Typography>
                      <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                        <Clock size={12} color="#94a3b8" />
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>{new Date(query.timestamp).toLocaleDateString()}</Typography>
                      </Box>
                    </Box>
                    <IconButton size="small" sx={{ opacity: 0.0, ':hover': { opacity: 1.0 }, transition: 'opacity 120ms' }}>
                      <Trash2 size={12} />
                    </IconButton>
                  </Box>
                </Box>
              </motion.div>
            ))}
          </Box>
        )}
      </Paper>
    </motion.div>
  )
}
