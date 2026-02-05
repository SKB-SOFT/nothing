// src/views/dashboard/components/MetricsChart.tsx
import React, { useState, useEffect } from 'react'
import {
  Box,
  Flex,
  Heading,
  ButtonGroup,
  Button,
  Skeleton,
  useColorModeValue,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { dashboardAPI } from '@/services/dashboard'

type TimeRange = '1h' | '6h' | '24h' | '7d'

interface MetricPoint {
  timestamp: string
  agent: string
  latency: number
  success: boolean
  tokens?: number
  model?: string
}

interface LatencyPercentiles {
  p50_ms: number
  p95_ms: number
  p99_ms: number
  avg_ms: number
}

const MetricsChart: React.FC = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>('24h')
  const [loading, setLoading] = useState(false)
  const [chartData, setChartData] = useState<any[]>([])
  const [percentiles, setPercentiles] = useState<LatencyPercentiles | null>(null)
  const [successRate, setSuccessRate] = useState<number>(0)

  const bg = useColorModeValue('white', 'gray.800')
  const textColor = 'black'

  const hoursMap = {
    '1h': 1,
    '6h': 6,
    '24h': 24,
    '7d': 168,
  }

  useEffect(() => {
    fetchMetrics()
  }, [timeRange])

  const fetchMetrics = async () => {
    setLoading(true)
    try {
      const hours = hoursMap[timeRange]

      // Fetch raw timeline data
      const timelineRes = await dashboardAPI.get('/metrics/timeline', {
        params: { hours },
      })
      const metrics: MetricPoint[] = timelineRes.data.metrics

      // Transform for chart (group by 5-min buckets)
      const groupedData = new Map<string, { latencies: number[]; count: number }>()

      metrics.forEach((m) => {
        const date = new Date(m.timestamp)
        const bucket = new Date(date.getTime() - (date.getTime() % (5 * 60 * 1000)))
        const key = bucket.toISOString()

        if (!groupedData.has(key)) {
          groupedData.set(key, { latencies: [], count: 0 })
        }

        const data = groupedData.get(key)!
        data.latencies.push(m.latency)
        data.count += 1
      })

      // Convert to chart format
      const chartArray = Array.from(groupedData.entries())
        .map(([time, data]) => ({
          time: new Date(time).toLocaleTimeString(),
          avgLatency: Math.round(data.latencies.reduce((a, b) => a + b, 0) / data.latencies.length),
          maxLatency: Math.max(...data.latencies),
          minLatency: Math.min(...data.latencies),
          requests: data.count,
        }))
        .sort((a, b) => a.time.localeCompare(b.time))

      setChartData(chartArray)

      // Fetch percentiles
      const percRes = await dashboardAPI.get('/metrics/latency-percentiles', {
        params: { hours },
      })
      setPercentiles(percRes.data)

      // Fetch success rate
      const successRes = await dashboardAPI.get('/metrics/success-rate', {
        params: { hours },
      })
      setSuccessRate(successRes.data.success_rate)
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      {/* Header */}
      <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm" mb={6}>
        <Flex justify="space-between" align="center" mb={6}>
          <Heading
            size="lg"
            color={textColor}
            fontWeight="800"
            fontFamily="Inter, Space Grotesk, ui-sans-serif"
          >
            📊 Performance Metrics
          </Heading>
          <ButtonGroup size="sm" isAttached variant="outline">
            {(['1h', '6h', '24h', '7d'] as TimeRange[]).map((range) => (
              <Button
                key={range}
                colorScheme={timeRange === range ? 'blue' : 'gray'}
                onClick={() => setTimeRange(range)}
                isLoading={loading}
              >
                {range}
              </Button>
            ))}
          </ButtonGroup>
        </Flex>

        {/* Key Metrics Cards */}
        {loading ? (
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} height="80px" borderRadius="md" />
            ))}
          </SimpleGrid>
        ) : (
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <Box bg={useColorModeValue('gray.50', 'gray.700')} p={4} borderRadius="md">
              <Stat>
                <StatLabel color="black">Success Rate</StatLabel>
                <StatNumber color="green.500" fontSize="24px">
                  {successRate.toFixed(1)}%
                </StatNumber>
              </Stat>
            </Box>

            <Box bg={useColorModeValue('gray.50', 'gray.700')} p={4} borderRadius="md">
              <Stat>
                <StatLabel color="black">P50 Latency</StatLabel>
                <StatNumber color="blue.500" fontSize="24px">
                  {percentiles ? `${percentiles.p50_ms.toFixed(0)}ms` : '--'}
                </StatNumber>
                <StatHelpText color="black">50% of requests</StatHelpText>
              </Stat>
            </Box>

            <Box bg={useColorModeValue('gray.50', 'gray.700')} p={4} borderRadius="md">
              <Stat>
                <StatLabel color="black">P95 Latency</StatLabel>
                <StatNumber color="orange.500" fontSize="24px">
                  {percentiles ? `${percentiles.p95_ms.toFixed(0)}ms` : '--'}
                </StatNumber>
                <StatHelpText color="black">95% of requests</StatHelpText>
              </Stat>
            </Box>

            <Box bg={useColorModeValue('gray.50', 'gray.700')} p={4} borderRadius="md">
              <Stat>
                <StatLabel color="black">P99 Latency</StatLabel>
                <StatNumber color="red.500" fontSize="24px">
                  {percentiles ? `${percentiles.p99_ms.toFixed(0)}ms` : '--'}
                </StatNumber>
                <StatHelpText color="black">Worst 1% of requests</StatHelpText>
              </Stat>
            </Box>
          </SimpleGrid>
        )}
      </Box>

      {/* Latency Timeline Chart */}
      <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm" mb={6}>
        <Heading size="md" mb={4} color={textColor}>
          ⏱️ Latency Over Time
        </Heading>
        {loading ? (
          <Skeleton height="300px" borderRadius="md" />
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                formatter={(value) => `${value}ms`}
                contentStyle={{
                  backgroundColor: useColorModeValue('white', '#2d3748'),
                  border: '1px solid #ccc',
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="avgLatency" stroke="#4299e1" name="Avg Latency" />
              <Line type="monotone" dataKey="maxLatency" stroke="#f56565" name="Max Latency" />
              <Line type="monotone" dataKey="minLatency" stroke="#48bb78" name="Min Latency" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <Box textAlign="center" py={10}>
            <Heading size="sm" color="black">
              No data yet. Make some queries first! 🚀
            </Heading>
          </Box>
        )}
      </Box>

      {/* Request Volume Chart */}
      <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm">
        <Heading size="md" mb={4} color={textColor}>
          📈 Request Volume
        </Heading>
        {loading ? (
          <Skeleton height="300px" borderRadius="md" />
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis label={{ value: 'Requests', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: useColorModeValue('white', '#2d3748'),
                  border: '1px solid #ccc',
                }}
              />
              <Bar dataKey="requests" fill="#9f7aea" name="Requests" />
            </BarChart>
          </ResponsiveContainer>
        ) : null}
      </Box>
    </Box>
  )
}

export default MetricsChart
