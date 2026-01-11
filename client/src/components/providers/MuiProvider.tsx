"use client"

import React from "react"
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material"

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#22d3ee" }, // cyan-400
    secondary: { main: "#f59e0b" }, // amber-500
    background: { default: "#0b1020", paper: "#0f172a" },
    text: { primary: "#e5e7eb", secondary: "#94a3b8" },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: "var(--font-sans), system-ui, -apple-system, Segoe UI, Roboto",
    fontSize: 14,
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
  },
})

export function MuiProvider({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  )
}
