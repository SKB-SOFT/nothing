'use client'

import * as React from 'react';
import { LineChart } from '@mui/x-charts/LineChart';
import { useTheme } from '@mui/material/styles';

export default function Chart({ data }: { data: Array<{ time: string; amount: number }> }) {
  const theme = useTheme();

  return (
    <LineChart
      xAxis={[{ data: data.map((d) => d.time), scaleType: 'point' }]}
      series={[
        {
          data: data.map((d) => d.amount),
        },
      ]}
      height={300}
      sx={{
        '& .MuiChartsAxis-line': {
          stroke: theme.palette.mode === 'dark' ? '#fff' : '#ccc',
        },
      }}
    />
  );
}
