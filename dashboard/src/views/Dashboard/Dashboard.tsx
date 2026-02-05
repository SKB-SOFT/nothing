'use client'

import * as React from 'react';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import { styled } from '@mui/material/styles';
import Title from './Title';
import Chart from './Chart';
import Deposits from './Deposits';
import Orders from './Orders';

const Item = styled(Paper)(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
  ...theme.typography.body2,
  padding: theme.spacing(2),
  textAlign: 'center',
  color: theme.palette.text.secondary,
}));

const mockChartData = [
  { time: '00:00', amount: 0 },
  { time: '03:00', amount: 300 },
  { time: '06:00', amount: 600 },
  { time: '09:00', amount: 800 },
  { time: '12:00', amount: 1200 },
  { time: '15:00', amount: 900 },
  { time: '18:00', amount: 1100 },
  { time: '21:00', amount: 700 },
];

const mockDeposits = [
  { date: 'Feb 1, 2026', increase: true, amount: 1247 },
  { date: 'Feb 2, 2026', increase: false, amount: 892 },
  { date: 'Feb 3, 2026', increase: true, amount: 1056 },
  { date: 'Feb 4, 2026', increase: true, amount: 1247 },
];

const mockOrders = [
  { id: '#001', name: 'John Doe', queries: 45, status: 'active' },
  { id: '#002', name: 'Priya Sharma', queries: 32, status: 'active' },
  { id: '#003', name: 'Hans Müller', queries: 28, status: 'inactive' },
];

export default function Dashboard() {
  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        {/* Chart */}
        <Grid item xs={12} md={8} lg={9}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 400,
            }}
          >
            <Title>Queries Today</Title>
            <Chart data={mockChartData} />
          </Paper>
        </Grid>
        {/* Recent Deposits */}
        <Grid item xs={12} md={4} lg={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 400,
            }}
          >
            <Title>Recent Users</Title>
            <Deposits data={mockDeposits} />
          </Paper>
        </Grid>
        {/* Recent Orders */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Title>Recent Activity</Title>
            <Orders data={mockOrders} />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
