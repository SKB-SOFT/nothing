'use client'

import React, { useEffect, useState } from 'react'
import {
  Box,
  Grid,
  GridItem,
  Heading,
  Flex,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react'
import { dashboardService, SystemMetrics, AgentStat, ActivityItem, ErrorLogItem } from '@/services/dashboard'
import { DashboardWebSocket } from '@/services/websocket'
import SystemStats from './SystemStats'
import AgentStatus from './AgentStatus'
import ErrorLog from './ErrorLog'
import LiveActivity from './LiveActivity'
import MetricsChart from './MetricsChart'

const Dashboard: React.FC = () => {
  const [systemStats, setSystemStats] = useState<SystemMetrics | null>(null)
  const [agents, setAgents] = useState<AgentStat[]>([])
  const [errors, setErrors] = useState<ErrorLogItem[]>([])
  const [liveActivity, setLiveActivity] = useState<ActivityItem[]>([])
  const [loading, setLoading] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)

  const toast = useToast()
  const bgColor = useColorModeValue('gray.50', 'gray.900')
  const cardBg = useColorModeValue('white', 'gray.800')

  // WebSocket instance
  const [ws] = useState(() => {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8001/api/dashboard/ws'
    return new DashboardWebSocket(wsUrl)
  })

  useEffect(() => {
    // Initial data fetch
    fetchDashboardData()

    // Set up WebSocket for real-time updates
    ws.connect(
      (data) => {
        handleWebSocketMessage(data)
        setWsConnected(true)
      },
      (error) => {
        console.error('WebSocket error:', error)
        setWsConnected(false)
        toast({
          title: 'Connection Lost',
          description: 'Real-time updates disconnected. Attempting to reconnect...',
          status: 'warning',
          duration: 5000,
          isClosable: true,
        })
      }
    )

    // Cleanup
    return () => {
      ws.disconnect()
    }
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      const [metricsData, agentsData, activityData, errorsData] = await Promise.all([
        dashboardService.getMetrics(),
        dashboardService.getAgents(),
        dashboardService.getActivity(20),
        dashboardService.getErrors(50),
      ])

      setSystemStats(metricsData)
      setAgents(agentsData)
      setLiveActivity(activityData)
      setErrors(errorsData)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'request':
        setLiveActivity(prev => [data.data, ...prev].slice(0, 20))
        break
      case 'error':
        setErrors(prev => [data.data, ...prev].slice(0, 50))
        setLiveActivity(prev => [data.data, ...prev].slice(0, 20))
        break
      default:
        console.log('Unknown message type:', data.type)
    }
  }

  const handleRefresh = () => {
    fetchDashboardData()
    toast({
      title: 'Refreshed',
      description: 'Dashboard data updated',
      status: 'success',
      duration: 2000,
      isClosable: true,
    })
  }

  return (
    <Box minH="100vh" bg={bgColor} p={8}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={8}>
        <Heading size="lg">Dashboard</Heading>
        <Flex gap={4} align="center">
          <Box
            w={3}
            h={3}
            borderRadius="full"
            bg={wsConnected ? 'green.400' : 'red.400'}
            title={wsConnected ? 'Connected' : 'Disconnected'}
          />
        </Flex>
      </Flex>

      {loading ? (
        <div className="text-center py-20">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-black">Loading dashboard...</p>
        </div>
      ) : (
        <Grid
          templateColumns={{
            base: '1fr',
            lg: 'repeat(12, 1fr)',
          }}
          gap={6}
        >
          {/* System Metrics */}
          {systemStats && (
            <GridItem colSpan={{ base: 1, lg: 12 }}>
              <SystemStats stats={systemStats} loading={loading} />
            </GridItem>
          )}

          {/* Charts and Activity */}
          <GridItem colSpan={{ base: 1, lg: 8 }}>
            <MetricsChart />
          </GridItem>

          <GridItem colSpan={{ base: 1, lg: 4 }}>
            <LiveActivity activities={liveActivity.slice(0, 10)} />
          </GridItem>

          {/* Agents and Errors */}
          <GridItem colSpan={{ base: 1, lg: 8 }}>
            <AgentStatus agents={agents} loading={loading} />
          </GridItem>

          <GridItem colSpan={{ base: 1, lg: 4 }}>
            <ErrorLog errors={errors.slice(0, 10)} />
          </GridItem>
        </Grid>
      )}
    </Box>
  )
}

export default Dashboard
