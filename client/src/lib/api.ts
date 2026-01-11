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
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Query endpoints
export const queryAPI = {
  submit: (queryText: string, selectedAgents: string[]) =>
    apiClient.post('/query', { query_text: queryText, selected_agents: selectedAgents }),
  
  getHistory: (limit = 20, offset = 0) =>
    apiClient.get('/queries', { params: { limit, offset } }),
  
  getDetails: (queryId: number) =>
    apiClient.get(`/query/${queryId}`),
}

// Admin endpoints
export const adminAPI = {
  getUsers: (limit = 10, offset = 0) =>
    apiClient.get('/admin/users', { params: { limit, offset } }),
  
  getMetrics: () =>
    apiClient.get('/admin/metrics'),
}
