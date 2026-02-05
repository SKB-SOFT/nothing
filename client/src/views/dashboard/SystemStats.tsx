import React from 'react'
import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Icon,
  Flex,
  useColorModeValue,
  Skeleton,
} from '@chakra-ui/react'
import {
  MdSpeed,
  MdCheckCircle,
  MdAccessTime,
  MdTrendingUp,
  MdMemory,
  MdGroup,
} from 'react-icons/md'
import { SystemMetrics } from '@/services/dashboard'

interface Props {
  stats: SystemMetrics | null
  loading?: boolean
}

interface StatCardProps {
  title: string
  stat: string
  icon: any
  change?: number
  helpText?: string
  isLoading?: boolean
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  stat,
  icon,
  change,
  helpText,
  isLoading,
}) => {
  const bg = useColorModeValue('white', 'gray.800')
  const iconBg = useColorModeValue('brand.50', 'brand.900')
  const iconColor = useColorModeValue('brand.500', 'brand.200')

  if (isLoading) {
    return (
      <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm">
        <Skeleton height="80px" />
      </Box>
    )
  }

  return (
    <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm" transition="all 0.3s" _hover={{ boxShadow: 'md' }}>
      <Flex justify="space-between" align="start">
        <Stat>
          <StatLabel fontSize="sm" fontWeight="bold" color="#16213a" letterSpacing={0.2} fontFamily="Inter, Space Grotesk, ui-sans-serif">
            {title}
          </StatLabel>
          <StatNumber fontSize="2xl" fontWeight="extrabold" mt={2} color="#0a192f" fontFamily="Inter, Space Grotesk, ui-sans-serif">
            {stat}
          </StatNumber>
          {(change !== undefined || helpText) && (
            <StatHelpText mb={0} fontSize="xs" color="#000" fontWeight="500" fontFamily="Inter, Space Grotesk, ui-sans-serif">
              {change !== undefined && (
                <>
                  <StatArrow type={change >= 0 ? 'increase' : 'decrease'} />
                  <span style={{ color: '#000', fontWeight: 600 }}>{Math.abs(change).toFixed(1)}%</span>
                </>
              )}
              {helpText && <span style={{ color: '#000', fontWeight: 500 }}>{` ${helpText}`}</span>}
            </StatHelpText>
          )}
        </Stat>
        <Flex
          bg={iconBg}
          p={3}
          borderRadius="lg"
          align="center"
          justify="center"
        >
          <Icon as={icon} w={6} h={6} color={iconColor} />
        </Flex>
      </Flex>
    </Box>
  )
}

const SystemStats: React.FC<Props> = ({ stats, loading }) => {
  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (days > 0) return `${days}d ${hours}h`
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  const formatResponseTime = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <SimpleGrid columns={{ base: 1, sm: 2, lg: 6 }} spacing={6}>
      <StatCard
        title="Total Requests"
        stat={stats?.total_requests.toLocaleString() || '0'}
        icon={MdTrendingUp}
        change={12.5}
        helpText="vs last hour"
        isLoading={loading}
      />
      
      <StatCard
        title="Active Agents"
        stat={stats?.active_agents.toString() || '0'}
        icon={MdGroup}
        isLoading={loading}
      />
      
      <StatCard
        title="System Uptime"
        stat={stats ? formatUptime(stats.uptime_seconds) : '0m'}
        icon={MdAccessTime}
        isLoading={loading}
      />
      
      <StatCard
        title="Current Load"
        stat={`${stats?.cpu_percent.toFixed(1) || '0'}%`}
        icon={MdMemory}
        change={stats ? (stats.cpu_percent > 50 ? 5.2 : -2.1) : 0}
        isLoading={loading}
      />
      
      <StatCard
        title="Avg Response Time"
        stat="0ms"
        icon={MdSpeed}
        change={-8.3}
        helpText="improvement"
        isLoading={loading}
      />
      
      <StatCard
        title="Success Rate"
        stat={`${stats?.success_rate.toFixed(1) || '0'}%`}
        icon={MdCheckCircle}
        change={stats ? (stats.success_rate >= 95 ? 1.2 : -3.4) : 0}
        isLoading={loading}
      />
    </SimpleGrid>
  )
}

export default SystemStats
