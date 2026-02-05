// src/views/dashboard/components/LiveActivity.tsx
import React from 'react'
import {
  Box,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Icon,
  useColorModeValue,
  Flex,
  Divider,
} from '@chakra-ui/react'
import {
  MdCheckCircle,
  MdError,
  MdAccessTime,
} from 'react-icons/md'
import { ActivityItem } from '@/services/dashboard'

interface Props {
  activities: ActivityItem[]
}

const LiveActivity: React.FC<Props> = ({ activities }) => {
  const bg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  const getStatusColor = (activity: ActivityItem) => {
    if (activity.type === 'request') {
      return activity.success ? 'green' : 'red'
    }
    return 'orange'
  }

  const getStatusIcon = (activity: ActivityItem) => {
    if (activity.type === 'request') {
      return activity.success ? MdCheckCircle : MdError
    }
    return MdAccessTime
  }

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm" h="100%">
      <Flex justify="space-between" align="center" mb={4}>
        <Heading size="lg" color="#0a192f" fontWeight="800" fontFamily="Inter, Space Grotesk, ui-sans-serif">Live Activity</Heading>
        <Badge colorScheme="green" fontSize="sm">
          <Flex align="center" gap={1}>
            <Box w={2} h={2} bg="green.500" borderRadius="full" animation="pulse 2s infinite" />
            Live
          </Flex>
        </Badge>
      </Flex>

      <VStack spacing={0} align="stretch" maxH="600px" overflowY="auto">
        {activities.length === 0 ? (
          <Box textAlign="center" py={8}>
            <Text color="black">No recent activity</Text>
          </Box>
        ) : (
          activities.map((activity, index) => (
            <React.Fragment key={index}>
              <Box
                py={3}
                transition="all 0.2s"
                _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}
              >
                <HStack spacing={3} align="start">
                  {/* Status Indicator */}
                  <Flex
                    mt={1}
                    w={8}
                    h={8}
                    align="center"
                    justify="center"
                    borderRadius="full"
                    bg={`${getStatusColor(activity)}.100`}
                  >
                    <Icon
                      as={getStatusIcon(activity)}
                      color={`${getStatusColor(activity)}.500`}
                      boxSize={4}
                    />
                  </Flex>

                  {/* Activity Details */}
                  <Box flex={1}>
                    <HStack justify="space-between" mb={1}>
                      <Text fontSize="sm" fontWeight="medium">
                        {activity.agent_name || activity.agent_id}
                      </Text>
                      <Text fontSize="xs" color="black">
                        {new Date(activity.timestamp).toLocaleTimeString()}
                      </Text>
                    </HStack>

                    <Text fontSize="sm" color="black" mb={2}>
                      {activity.type === 'request' ? 'Request processed' : 'Error occurred'}
                    </Text>

                    <HStack spacing={2}>
                      <Badge
                        size="sm"
                        colorScheme={getStatusColor(activity)}
                        variant="subtle"
                      >
                        {activity.type === 'request' ? (activity.success ? 'Success' : 'Failed') : 'Error'}
                      </Badge>
                      {activity.response_time_ms && (
                        <Badge size="sm" variant="subtle">
                          {formatDuration(activity.response_time_ms)}
                        </Badge>
                      )}
                    </HStack>
                  </Box>
                </HStack>
              </Box>
              {index < activities.length - 1 && <Divider />}
            </React.Fragment>
          ))
        )}
      </VStack>

      <style>
        {`
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
            }
            50% {
              opacity: 0.5;
            }
          }
        `}
      </style>
    </Box>
  )
}

export default LiveActivity
