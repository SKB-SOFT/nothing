import type { Metadata } from "next"
import { Space_Grotesk, JetBrains_Mono } from "next/font/google"
import "./globals.css"
import { AuthProvider } from "@/context/AuthContext"
import { MuiProvider } from "@/components/providers/MuiProvider"
import { ToastProvider } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/toaster"

const sans = Space_Grotesk({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
})

const mono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
})

export const metadata: Metadata = {
  title: "Multi-AI Orchestrator",
  description: "Query multiple AI models at once",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${sans.variable} ${mono.variable} bg-slate-950 text-slate-100 antialiased`}>
        <div className="relative min-h-screen overflow-hidden">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.18),transparent_35%),radial-gradient(circle_at_80%_0%,rgba(251,191,36,0.18),transparent_30%),radial-gradient(circle_at_50%_80%,rgba(236,72,153,0.12),transparent_35%)] blur-3xl" />
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(120deg,rgba(148,163,184,0.08)_0%,transparent_40%,rgba(148,163,184,0.08)_80%)] opacity-60" />
          <div className="relative z-10">
            <MuiProvider>
              <AuthProvider>
                <ToastProvider>
                  {children}
                  <Toaster />
                </ToastProvider>
              </AuthProvider>
            </MuiProvider>
          </div>
        </div>
      </body>
    </html>
  )
}
