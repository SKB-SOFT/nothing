// src/views/dashboard/components/AgentStatus.tsx
import React from 'react'
import {
  Box,
  Flex,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Icon,
  useColorModeValue,
  Skeleton,
  Text,
  Tooltip,
  Progress,
} from '@chakra-ui/react'
import {
  MdCheckCircle,
  MdPause,
  MdError,
  MdAccessTime,
} from 'react-icons/md'
import { AgentStat } from '@/services/dashboard'

interface Props {
  agents: AgentStat[]
  loading?: boolean
}

const AgentStatus: React.FC<Props> = ({ agents, loading }) => {
  const bg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green'
      case 'idle':
        return 'yellow'
      case 'error':
        return 'red'
      case 'offline':
        return 'gray'
      default:
        return 'gray'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return MdCheckCircle
      case 'idle':
        return MdPause
      case 'error':
        return MdError
      case 'offline':
        return MdAccessTime
      default:
        return MdAccessTime
    }
  }

  if (loading) {
    return (
      <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm">
        <Skeleton height="400px" />
      </Box>
    )
  }

  return (
    <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm">
      <Flex justify="space-between" align="center" mb={4}>
        <Heading size="lg" color="#0a192f" fontWeight="800" fontFamily="Inter, Space Grotesk, ui-sans-serif">Agent Status</Heading>
        <Badge colorScheme="blue" fontSize="md" px={3} py={1} borderRadius="md" bg="#3b82f6" color="#fff" fontWeight="700" fontFamily="Inter, Space Grotesk, ui-sans-serif">
          {agents.length} Active
        </Badge>
      </Flex>

      <Box overflowX="auto">
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>Agent</Th>
              <Th>Model</Th>
              <Th>Status</Th>
              <Th isNumeric>Requests</Th>
              <Th isNumeric>Avg Response</Th>
              <Th isNumeric>Success Rate</Th>
              <Th>Last Active</Th>
            </Tr>
          </Thead>
          <Tbody>
            {agents.length === 0 ? (
              <Tr>
                <Td colSpan={7} textAlign="center" py={8}>
                  <Text color="black">No agents active</Text>
                </Td>
              </Tr>
            ) : (
              agents.map((agent) => (
                <Tr key={agent.agent_id} _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}>
                  <Td fontWeight="medium">{agent.name}</Td>
                  <Td>
                    <Badge colorScheme="purple" variant="subtle">
                      {agent.model}
                    </Badge>
                  </Td>
                  <Td>
                    <Flex align="center" gap={2}>
                      <Icon
                        as={getStatusIcon(agent.status)}
                        color={`${getStatusColor(agent.status)}.500`}
                      />
                      <Badge colorScheme={getStatusColor(agent.status)}>
                        {agent.status}
                      </Badge>
                    </Flex>
                  </Td>
                  <Td isNumeric>{agent.total_requests.toLocaleString()}</Td>
                  <Td isNumeric>
                    {agent.avg_response_time < 1000
                      ? `${agent.avg_response_time.toFixed(0)}ms`
                      : `${(agent.avg_response_time / 1000).toFixed(2)}s`}
                  </Td>
                  <Td isNumeric>
                    <Tooltip label={`${agent.success_rate.toFixed(2)}%`}>
                      <Box>
                        <Progress
                          value={agent.success_rate}
                          size="sm"
                          colorScheme={agent.success_rate >= 90 ? 'green' : agent.success_rate >= 70 ? 'yellow' : 'red'}
                          borderRadius="full"
                        />
                      </Box>
                    </Tooltip>
                  </Td>
                  <Td fontSize="xs" color="black">
                    {new Date(agent.last_used).toLocaleTimeString()}
                  </Td>
                </Tr>
              ))
            )}
          </Tbody>
        </Table>
      </Box>
    </Box>
  )
}

export default AgentStatus
