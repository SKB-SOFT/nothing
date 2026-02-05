// src/views/dashboard/components/ErrorLog.tsx
import React, { useState } from 'react'
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
  Collapse,
  IconButton,
  Button,
  Skeleton,
} from '@chakra-ui/react'
import {
  MdError,
  MdWarning,
  MdInfo,
  MdExpandMore,
  MdExpandLess,
} from 'react-icons/md'
import { ErrorLogItem } from '@/services/dashboard'

interface Props {
  errors: ErrorLogItem[]
  loading?: boolean
}

const ErrorLog: React.FC<Props> = ({ errors, loading }) => {
  const [expandedErrors, setExpandedErrors] = useState<Set<string>>(new Set())
  const bg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const hoverBg = useColorModeValue('gray.50', 'gray.700')

  const toggleExpand = (errorId: string | number) => {
    const idStr = String(errorId)
    setExpandedErrors((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(idStr)) {
        newSet.delete(idStr)
      } else {
        newSet.add(idStr)
      }
      return newSet
    })
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'red'
      case 'high':
        return 'orange'
      case 'medium':
        return 'yellow'
      case 'low':
        return 'blue'
      default:
        return 'gray'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return MdError
      case 'medium':
        return MdWarning
      case 'low':
        return MdInfo
      default:
        return MdInfo
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
    <Box bg={bg} p={6} borderRadius="lg" boxShadow="sm" h="100%">
      <Flex justify="space-between" align="center" mb={4}>
        <Heading size="lg" color="#0a192f" fontWeight="800" fontFamily="Inter, Space Grotesk, ui-sans-serif">Recent Errors</Heading>
        <Badge colorScheme="red" fontSize="md" px={3} py={1} borderRadius="md" bg="#ef4444" color="#fff" fontWeight="700" fontFamily="Inter, Space Grotesk, ui-sans-serif">
          {errors.length} Errors
        </Badge>
      </Flex>

      <VStack spacing={3} align="stretch" maxH="600px" overflowY="auto">
        {errors.length === 0 ? (
          <Box textAlign="center" py={8}>
            <Text color="black">No errors logged</Text>
          </Box>
        ) : (
          errors.map((error, idx) => {
            const errorId = String(idx)
            const isExpanded = expandedErrors.has(errorId)
            return (
              <Box
                key={errorId}
                p={4}
                borderWidth="1px"
                borderColor={borderColor}
                borderRadius="md"
                transition="all 0.2s"
                _hover={{ bg: hoverBg }}
              >
                <HStack justify="space-between" mb={2}>
                  <HStack spacing={2}>
                    <Icon
                      as={getSeverityIcon(error.severity)}
                      color={`${getSeverityColor(error.severity)}.500`}
                      boxSize={5}
                    />
                    <Badge colorScheme={getSeverityColor(error.severity)}>
                      {error.severity}
                    </Badge>
                    <Badge variant="outline">{error.error_type}</Badge>
                  </HStack>
                  <IconButton
                    aria-label="Expand error"
                    icon={<Icon as={isExpanded ? MdExpandLess : MdExpandMore} />}
                    size="sm"
                    variant="ghost"
                    onClick={() => toggleExpand(errorId)}
                  />
                </HStack>

                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  {error.agent_id}
                </Text>

                <Text fontSize="sm" color="black" mb={2} noOfLines={isExpanded ? undefined : 2}>
                  {error.error_message}
                </Text>

                <Collapse in={isExpanded}>
                  <Box mt={3} p={3} bg={useColorModeValue('gray.100', 'gray.900')} borderRadius="md">
                    <Text fontSize="xs" fontFamily="mono" color="black">
                      {error.error_message}
                    </Text>
                  </Box>
                </Collapse>

                <Text fontSize="xs" color="black" mt={2}>
                  {new Date(error.timestamp).toLocaleString()}
                </Text>
              </Box>
            )
          })
        )}
      </VStack>

      {errors.length > 0 && (
        <Button
          mt={4}
          w="100%"
          size="sm"
          variant="outline"
          onClick={() => {
            console.log('View all errors')
          }}
        >
          View All Errors
        </Button>
      )}
    </Box>
  )
}

export default ErrorLog
