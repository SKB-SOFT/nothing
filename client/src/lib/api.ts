import axios from 'axios'

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.trim() ||
  'http://127.0.0.1:8001' // dev fallback (match your run_dev.ps1 default)

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? window.localStorage.getItem('token') : null
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Optional: normalize error messages for UI
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err?.response?.data?.detail ||
      err?.response?.data?.message ||
      err?.message ||
      'Request failed'
    err.normalizedMessage = msg
    return Promise.reject(err)
  }
)

// Query endpoints
export const queryAPI = {
  submit: (queryText: string, selectedAgents: string[]) =>
    apiClient.post('/api/query', { query_text: queryText, selected_agents: selectedAgents }),
  
  getHistory: (limit = 20, offset = 0) =>
    apiClient.get('/api/queries', { params: { limit, offset } }),
  
  getDetails: (queryId: number) =>
    apiClient.get(`/api/query/${queryId}`),
}

// Admin endpoints
export const adminAPI = {
  getUsers: (limit = 10, offset = 0) =>
    apiClient.get('/api/admin/users', { params: { limit, offset } }),
  
  getMetrics: () =>
    apiClient.get('/api/admin/metrics'),
}
