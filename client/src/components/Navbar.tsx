'use client'

import { useAuth } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Zap, LogOut, Command } from 'lucide-react'
import Link from 'next/link'
import { CommandPalette } from '@/components/CommandPalette'
import { ThemeToggle } from '@/components/ui/ThemeToggle'

export function Navbar() {
  const { user, logout } = useAuth()
  const router = useRouter()

    return (
      <>
        <AppBar position="sticky" elevation={0} sx={{ bgcolor: "transparent", borderBottom: "1px solid rgba(148,163,184,0.2)", backdropFilter: "blur(8px)" }}>
          <Toolbar sx={{ maxWidth: 1200, mx: "auto", width: "100%" }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mr: "auto" }}>
              <Link href="/" className="flex items-center gap-3">
                <Box sx={{ width: 36, height: 36, borderRadius: 2, display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg,#22d3ee,#2563eb)", boxShadow: "0 8px 24px rgba(34,211,238,0.25)" }}>
                  <Zap size={16} color="#fff" />
                </Box>
                <Box sx={{ lineHeight: 1 }}>
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>Multi-AI</Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>Orchestrator</Typography>
                </Box>
              </Link>
            </Box>

            <Chip label="Connected" size="small" sx={{ mr: 1.5 }} color="success" variant="outlined" />
            <IconButton
              onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: !navigator.platform.toUpperCase().includes('MAC'), metaKey: navigator.platform.toUpperCase().includes('MAC') }))}
              sx={{ display: { xs: 'none', md: 'inline-flex' }, mr: 1 }}
              title="Open Command Palette (Ctrl/Cmd+K)"
            >
              <Command size={18} />
            </IconButton>
            <Box sx={{ mr: 2 }}>
              <ThemeToggle />
            </Box>

            {user ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Chip
                  avatar={<Box sx={{ width: 24, height: 24, borderRadius: '50%', background: 'linear-gradient(135deg,#22d3ee,#2563eb)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12 }}>{user.full_name.slice(0,2).toUpperCase()}</Box>}
                  label={<Box sx={{ lineHeight: 1 }}><Typography variant="body2" sx={{ fontWeight: 600 }}>{user.full_name}</Typography><Typography variant="caption" sx={{ color: 'text.secondary' }}>{user.email}</Typography></Box>}
                  variant="outlined"
                  sx={{ bgcolor: 'rgba(2,6,23,0.7)' }}
                />
                <Button variant="contained" color="primary" onClick={handleLogout} startIcon={<LogOut size={18} />}>Logout</Button>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Link href="/login"><Button variant="contained" color="primary">Sign In</Button></Link>
                <Link href="/register" className="hidden sm:block"><Button variant="outlined" color="inherit">Register</Button></Link>
              </Box>
            )}
          </Toolbar>
        </AppBar>
        <CommandPalette />
      </>
    )
          )}
        </div>
      </div>
      <CommandPalette />
    </nav>
  )
}
