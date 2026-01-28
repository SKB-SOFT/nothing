'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

interface User {
  id: number
  email: string
  full_name: string
  quota_daily: number
  is_admin: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, full_name: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Load token from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('token')
    if (savedToken) {
      setToken(savedToken)
      // Validate token
      validateToken(savedToken)
    } else {
      setLoading(false)
    }
  }, [])

  const validateToken = async (token: string) => {
    try {
      const response = await apiClient.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setUser(response.data.user)
    } catch (error) {
      localStorage.removeItem('token')
      setToken(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.post('/api/auth/login', { email, password })
      const { access_token, user } = response.data
      localStorage.setItem('token', access_token)
      setToken(access_token)
      setUser(user)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || error.normalizedMessage || 'Login failed')
    }
  }

  const register = async (email: string, password: string, full_name: string) => {
    try {
      const response = await apiClient.post('/api/auth/register', { email, password, full_name })
      const { access_token, user } = response.data
      localStorage.setItem('token', access_token)
      setToken(access_token)
      setUser(user)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || error.normalizedMessage || 'Registration failed')
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
