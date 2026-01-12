import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? window.localStorage.getItem('token') : null
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

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
