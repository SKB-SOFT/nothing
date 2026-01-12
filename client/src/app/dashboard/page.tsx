'use client';

import { useMemo, useRef, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  LinearProgress,
  Menu,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Toolbar,
  Typography,
  createTheme,
  ThemeProvider,
  Tooltip,
  Popover,
} from '@mui/material';
import { apiClient, queryAPI } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import AddIcon from '@mui/icons-material/Add';
import SendIcon from '@mui/icons-material/Send';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import SearchIcon from '@mui/icons-material/Search';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import StorageIcon from '@mui/icons-material/Storage';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import ExploreIcon from '@mui/icons-material/Explore';
import Groups2Icon from '@mui/icons-material/Groups2';
import PaidIcon from '@mui/icons-material/Paid';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import WorkspacePremiumIcon from '@mui/icons-material/WorkspacePremium';
import DownloadIcon from '@mui/icons-material/Download';

const drawerWidth = 72;

type Msg = {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  timestamp?: number;
  resources?: { query_time: number; tokens: number; model: string }[];
};

type ProviderInfo = {
  name: string;
  tier?: string;
  quota?: string;
  enabled?: boolean;
  initialized: boolean;
  default_model?: string;
  status?: string;
  error?: string | null;
};

const MODELS = [
  { id: 'groq', name: 'Groq (Mixtral)', provider: 'Groq', icon: '⚡' },
  { id: 'gemini', name: 'Gemini 2.0', provider: 'Google', icon: '🔮' },
  { id: 'mistral', name: 'Mistral Large', provider: 'Mistral AI', icon: '🌪️' },
  { id: 'cerebras', name: 'Cerebras (LLaMA)', provider: 'Cerebras', icon: '🧠' },
  { id: 'cohere', name: 'Command R+', provider: 'Cohere', icon: '💫' },
  { id: 'huggingface', name: 'Zephyr 7B', provider: 'HuggingFace', icon: '🤗' },
];

export default function DashboardPerplexity() {
  const router = useRouter();
  const { user, token, loading: authLoading, logout } = useAuth();

  const [mounted, setMounted] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [history] = useState<string[]>([
    'Summarize latest AI trends 2025',
    'Compare LLM performance benchmarks',
    'Best practices for prompt engineering',
  ]);
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: 'assistant',
      content:
        "Welcome! I'm your AI research assistant. I can search across multiple models and provide sources.",
      model: 'system',
    },
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const [selectedModels, setSelectedModels] = useState<string[]>(MODELS.map((m) => m.id));
  const [providers, setProviders] = useState<Record<string, ProviderInfo> | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [focusMode, setFocusMode] = useState<'research' | 'writing' | 'default'>('default');
  const [modelHover, setModelHover] = useState<{ anchor: HTMLElement | null; id: string | null }>({
    anchor: null,
    id: null,
  });
  const [focusHoverAnchor, setFocusHoverAnchor] = useState<HTMLElement | null>(null);

  const endRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiClient.get('/api/providers');
        const map = (res.data?.providers ?? null) as Record<string, ProviderInfo> | null;
        if (!cancelled) setProviders(map);
      } catch {
        if (!cancelled) setProviders(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!providers) return;
    const initializedIds = MODELS.filter((m) => providers[m.id]?.initialized).map((m) => m.id);
    setSelectedModels((prev) => {
      const filteredPrev = prev.filter((id) => providers[id]?.initialized);
      if (filteredPrev.length > 0) return filteredPrev;
      return initializedIds.length > 0 ? initializedIds : prev;
    });
  }, [providers]);

  useEffect(() => {
    if (!mounted) return;
    if (authLoading) return;
    // Guest mode: do not redirect to login.
  }, [authLoading, mounted]);
  
  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages.length]);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: 'dark',
          background: { default: '#070B14', paper: '#0B1220' },
          primary: { main: '#00E5FF' },
        },
        shape: { borderRadius: 12 },
        typography: {
          fontFamily: 'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial',
        },
      }),
    []
  );

  const handleSend = async () => {
    const text = prompt.trim();
    if (!text || isLoading) return;

    // Guest mode: allow queries without a token.

    setMessages((prev) => [...prev, { role: 'user', content: text, timestamp: Date.now() }]);
    setPrompt('');
    setIsLoading(true);

    try {
      const response = await queryAPI.submit(text, selectedModels);
      const data = response.data;

      // Prefer clean single-answer field from backend
      let content: string = (typeof data.final_answer === 'string' && data.final_answer.trim())
        ? data.final_answer.trim()
        : 'No answer returned.';

      // Compact failure summary (optional)
      if (Array.isArray(data.errors) && data.errors.length > 0) {
        const lines = data.errors
          .slice(0, 6)
          .map((e: any) => `- ${e.agent_id}: ${e.error_type || 'error'} (${(e.error_message || '').toString().slice(0, 140)})`);
        content += `\n\nSome providers failed:\n${lines.join('\n')}`;
      }

      const resources = data.responses?.map((res: any) => ({
        query_time: res.response_time_ms / 1000,
        tokens: res.token_count || 0,
        model: res.agent_name,
      })) || [];

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content,
          model: selectedModels[0],
          resources,
          timestamp: Date.now(),
        },
      ]);
    } catch (error: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ Error: ${error.response?.data?.detail || error.message || 'Failed to query models'}`,
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Prevent hydration errors by only rendering after mount
  if (!mounted || authLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', bgcolor: '#070B14' }}>
        <CircularProgress />
      </Box>
    );
  }

  // No redirect in guest mode

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: '#070B14' }}>
        {/* Slim left icon rail */}
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
              borderRight: '1px solid rgba(255,255,255,0.08)',
              bgcolor: '#0B1220',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'stretch',
            },
          }}
        >
          <Box sx={{ p: 1.5, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <AutoAwesomeIcon sx={{ color: '#00E5FF', fontSize: 24 }} />
          </Box>
          <Divider />
          <Stack sx={{ px: 0.5, py: 1, alignItems: 'center' }} spacing={1.5}>
            <Tooltip title="New" placement="right">
              <IconButton size="small" onClick={() => setMessages([{ role: 'assistant', content: 'New chat started.' }])}>
                <AddIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Library" placement="right">
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <IconButton size="small"><LibraryBooksIcon /></IconButton>
                <Typography variant="caption" sx={{ fontSize: 10, color: 'text.secondary' }}>Library</Typography>
              </Box>
            </Tooltip>
            <Tooltip title="More" placement="right">
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <IconButton size="small"><MoreHorizIcon /></IconButton>
                <Typography variant="caption" sx={{ fontSize: 10, color: 'text.secondary' }}>More</Typography>
              </Box>
            </Tooltip>
          </Stack>
          <Box sx={{ flex: 1 }} />
          <Stack sx={{ px: 0.5, pb: 1.5, alignItems: 'center' }} spacing={1.5}>
            <Tooltip title="Notifications" placement="right">
              <IconButton size="small"><NotificationsNoneIcon /></IconButton>
            </Tooltip>
            <Tooltip title="Account" placement="right">
              <IconButton size="small" onClick={(e) => setAnchorEl(e.currentTarget)}>
                <Avatar sx={{ width: 24, height: 24, bgcolor: '#00E5FF' }}>
                  {(user?.full_name?.[0] || user?.email?.[0] || 'U').toUpperCase()}
                </Avatar>
              </IconButton>
            </Tooltip>
          </Stack>
          <Menu anchorEl={anchorEl} open={!!anchorEl} onClose={() => setAnchorEl(null)}>
            <MenuItem>
              <AccountCircleIcon sx={{ mr: 1 }} /> Profile
            </MenuItem>
            <MenuItem>
              <SettingsIcon sx={{ mr: 1 }} /> Settings
            </MenuItem>
            <Divider />
            <MenuItem
              onClick={() => {
                setAnchorEl(null);
                logout();
                router.push('/login');
              }}
            >
              <LogoutIcon sx={{ mr: 1 }} /> Logout
            </MenuItem>
          </Menu>
        </Drawer>

        {/* Main Content */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Top Bar */}
          <AppBar
            position="sticky"
            elevation={0}
            sx={{
              bgcolor: 'rgba(7,11,20,0.7)',
              backdropFilter: 'blur(12px)',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <Toolbar>
              <LightbulbIcon sx={{ mr: 1, color: '#00E5FF' }} />
              <Typography fontWeight={700}>Research Assistant</Typography>
              <Box sx={{ flex: 1 }} />
              <Chip
                label={`${selectedModels.length} model${selectedModels.length > 1 ? 's' : ''}`}
                size="small"
                variant="outlined"
                sx={{ mr: 1 }}
              />
              <Chip
                label={`${focusMode} mode`}
                size="small"
                icon={<SearchIcon />}
                variant="filled"
                color="primary"
              />
            </Toolbar>
            {isLoading && <LinearProgress sx={{ height: 2 }} />}
          </AppBar>

          {/* Messages */}
          <Box sx={{ flex: 1, px: { xs: 3, md: 4 }, py: 4, overflowY: 'auto' }}>
            <Stack spacing={3} sx={{ maxWidth: 1120, mx: 'auto' }}>
              {messages.map((m, idx) => (
                <Box key={idx}>
                  <Stack
                    direction="row"
                    justifyContent={m.role === 'user' ? 'flex-end' : 'flex-start'}
                    sx={{ mb: 0.75 }}
                  >
                    {m.role === 'assistant' && (
                      <Avatar sx={{ mr: 1.25, width: 36, height: 36, bgcolor: '#00E5FF' }}>
                        {m.model?.charAt(0).toUpperCase() || 'A'}
                      </Avatar>
                    )}
                    <Paper
                      variant="outlined"
                      sx={{
                        px: 3,
                        py: 2,
                        maxWidth: '80%',
                        bgcolor: m.role === 'user' ? 'rgba(0, 229, 255, 0.08)' : 'rgba(255,255,255,0.03)',
                        borderColor: m.role === 'user' ? 'rgba(0, 229, 255, 0.2)' : 'rgba(255,255,255,0.1)',
                        borderRadius: 2.5,
                      }}
                    >
                      <Typography whiteSpace="pre-wrap" lineHeight={1.9} variant="body1">
                        {m.content}
                      </Typography>
                      {m.resources && (
                        <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                          {m.resources.map((r, i) => (
                            <Stack key={i} direction="row" spacing={1} sx={{ mt: 0.75 }} alignItems="center">
                              <StorageIcon sx={{ fontSize: 14, color: '#00E5FF' }} />
                              <Typography variant="caption" color="text.secondary">
                                {r.model} • {r.tokens} tokens • {r.query_time.toFixed(2)}s
                              </Typography>
                            </Stack>
                          ))}
                        </Box>
                      )}
                    </Paper>
                    {m.role === 'user' && (
                      <Avatar sx={{ ml: 1.25, width: 36, height: 36, bgcolor: '#00E5FF' }}>R</Avatar>
                    )}
                  </Stack>
                  {m.role === 'assistant' && m.model && (
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 5 }}>
                      {m.model.toUpperCase()}
                    </Typography>
                  )}
                </Box>
              ))}
              {isLoading && (
                <Stack direction="row" spacing={1} alignItems="flex-end">
                  <CircularProgress size={24} sx={{ color: '#00E5FF' }} />
                  <Typography variant="body2" color="text.secondary">
                    Searching across models...
                  </Typography>
                </Stack>
              )}
              <div ref={endRef} />
            </Stack>
          </Box>

          {/* Composer */}
          <Box
            sx={{
              borderTop: '1px solid rgba(255,255,255,0.08)',
              bgcolor: 'rgba(7,11,20,0.75)',
              backdropFilter: 'blur(12px)',
              px: { xs: 3, md: 4 },
              py: 2.5,
            }}
          >
            <Stack spacing={1.75} sx={{ maxWidth: 1120, mx: 'auto' }}>
              {messages.length === 1 && (
                <Stack direction="row" spacing={1}>
                  {['Explain quantum computing', 'Latest AI breakthroughs', 'Best LLM for coding'].map((suggest) => (
                    <Button
                      key={suggest}
                      size="small"
                      variant="outlined"
                      onClick={() => setPrompt(suggest)}
                      sx={{ textTransform: 'none', borderRadius: 2, fontSize: 12 }}
                    >
                      ✨ {suggest}
                    </Button>
                  ))}
                </Stack>
              )}

              {/* Inline quick toggles */}
              <Stack direction="row" spacing={1} alignItems="center">
                <Tooltip title="Select models" placement="top">
                  <Chip
                    label={`${selectedModels.length} models`}
                    color="primary"
                    variant="outlined"
                    onClick={(e) => setModelHover({ anchor: e.currentTarget as HTMLElement, id: null })}
                    onMouseEnter={(e) => setModelHover({ anchor: e.currentTarget, id: null })}
                    onMouseLeave={() => setModelHover({ anchor: null, id: null })}
                    sx={{ borderRadius: 2 }}
                  />
                </Tooltip>
                {MODELS.filter((m) => providers?.[m.id]?.initialized ?? true).map((m) => {
                  const initialized = providers?.[m.id]?.initialized ?? true;
                  const title = initialized
                    ? `${m.name} (${m.provider})`
                    : `${m.name} (${m.provider}) — not available on server`;

                  return (
                    <Tooltip key={m.id} title={title} placement="top">
                      <Chip
                        label={`${m.icon} ${m.name}`}
                        variant={selectedModels.includes(m.id) ? 'filled' : 'outlined'}
                        color={selectedModels.includes(m.id) ? 'primary' : 'default'}
                        disabled={!initialized}
                        onClick={() => {
                          if (!initialized) return;
                          setSelectedModels((prev) =>
                            prev.includes(m.id) ? prev.filter((x) => x !== m.id) : [...prev, m.id]
                          );
                        }}
                        onMouseEnter={(e) => setModelHover({ anchor: e.currentTarget, id: m.id })}
                        onMouseLeave={() => setModelHover({ anchor: null, id: null })}
                        sx={{ borderRadius: 2 }}
                      />
                    </Tooltip>
                  );
                })}
                <Box sx={{ width: 12 }} />
                <Tooltip title="Focus mode" placement="top">
                  <Chip
                    label={`${focusMode} mode`}
                    icon={<SearchIcon />}
                    onClick={(e) => setFocusHoverAnchor(e.currentTarget as HTMLElement)}
                    onMouseEnter={(e) => setFocusHoverAnchor(e.currentTarget)}
                    onMouseLeave={() => setFocusHoverAnchor(null)}
                    sx={{ borderRadius: 2 }}
                  />
                </Tooltip>
              </Stack>

              <Stack direction="row" spacing={1}>
                <TextField
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  fullWidth
                  placeholder="Ask me anything about AI, research, or code..."
                  multiline
                  maxRows={6}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2.5,
                      bgcolor: 'rgba(0, 229, 255, 0.03)',
                    },
                  }}
                />
                <IconButton
                  onClick={handleSend}
                  disabled={!prompt.trim() || isLoading}
                  sx={{
                    width: 52,
                    height: 52,
                    borderRadius: 2.5,
                    bgcolor: 'rgba(0, 229, 255, 0.14)',
                    '&:hover': { bgcolor: 'rgba(0, 229, 255, 0.22)' },
                    '&.Mui-disabled': { bgcolor: 'rgba(0, 229, 255, 0.05)' },
                  }}
                >
                  <SendIcon />
                </IconButton>
              </Stack>
              <Typography variant="caption" color="text.secondary">
                Shift+Enter for new line • Select models above
              </Typography>
            </Stack>
          </Box>
        </Box>

        {/* Hover Popovers */}
        <Popover
          open={Boolean(modelHover.anchor)}
          anchorEl={modelHover.anchor}
          onClose={() => setModelHover({ anchor: null, id: null })}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
          transformOrigin={{ vertical: 'bottom', horizontal: 'center' }}
          disableRestoreFocus
          PaperProps={{ sx: { p: 1.5, bgcolor: '#0B1220', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 2 } }}
        >
          <Stack spacing={1} sx={{ minWidth: 220 }}>
            {modelHover.id ? (
              <>
                <Typography variant="body2" fontWeight={700}>
                  {MODELS.find((x) => x.id === modelHover.id)?.icon}{' '}
                  {MODELS.find((x) => x.id === modelHover.id)?.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {MODELS.find((x) => x.id === modelHover.id)?.provider || ''}
                </Typography>
                <Stack direction="row" spacing={1}>
                  <Button
                    size="small"
                    variant={selectedModels.includes(modelHover.id) ? 'contained' : 'outlined'}
                    onClick={() => {
                      const id = modelHover.id;
                      if (!id) return;
                      setSelectedModels((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
                    }}
                  >
                    {selectedModels.includes(modelHover.id) ? 'Selected' : 'Select'}
                  </Button>
                </Stack>
              </>
            ) : (
              <>
                <Typography variant="body2" fontWeight={700}>Active models</Typography>
                <Stack direction="row" spacing={1}>
                  {selectedModels.map((id) => (
                    <Chip key={id} label={MODELS.find((m) => m.id === id)?.name || id} size="small" />
                  ))}
                </Stack>
              </>
            )}
          </Stack>
        </Popover>

        <Popover
          open={Boolean(focusHoverAnchor)}
          anchorEl={focusHoverAnchor}
          onClose={() => setFocusHoverAnchor(null)}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
          transformOrigin={{ vertical: 'bottom', horizontal: 'center' }}
          disableRestoreFocus
          PaperProps={{ sx: { p: 1.5, bgcolor: '#0B1220', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 2 } }}
        >
          <Stack spacing={1} sx={{ minWidth: 240 }}>
            <Typography variant="body2" fontWeight={700}>Focus mode</Typography>
            <Stack direction="row" spacing={1}>
              {(['default', 'research', 'writing'] as const).map((mode) => (
                <Chip
                  key={mode}
                  label={mode}
                  color={focusMode === mode ? 'primary' : 'default'}
                  variant={focusMode === mode ? 'filled' : 'outlined'}
                  onClick={() => setFocusMode(mode)}
                  sx={{ textTransform: 'capitalize', borderRadius: 2 }}
                />
              ))}
            </Stack>
            <Typography variant="caption" color="text.secondary">
              Default: balanced • Research: facts & sources • Writing: style & clarity
            </Typography>
          </Stack>
        </Popover>
      </Box>
    </ThemeProvider>
  );
}
