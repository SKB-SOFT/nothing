'use client'

import * as React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Title from './Title';

interface DepositsProps {
  data: Array<{ date: string; increase: boolean; amount: number }>;
}

export default function Deposits(props: DepositsProps) {
  return (
    <React.Fragment>
      <Title>Recent Users</Title>
      <Box sx={{ flex: 1 }}>
        {props.data.map((deposit) => (
          <Box
            key={deposit.date}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              py: 1,
              borderBottom: '1px solid rgba(255,255,255,0.1)',
            }}
          >
            <Typography component="p" variant="body2" color="text.secondary">
              {deposit.date}
            </Typography>
            <Typography component="p" variant="h5">
              {deposit.amount.toLocaleString()}
            </Typography>
          </Box>
        ))}
      </Box>
    </React.Fragment>
  );
}
