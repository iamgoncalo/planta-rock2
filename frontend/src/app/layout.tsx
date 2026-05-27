import type { Metadata, Viewport } from 'next'
import './globals.css'
import Nav from '@/components/Nav'
import { WSProvider } from '@/context/WSContext'

export const metadata: Metadata = {
  title: 'PlantaOS · Rock in Rio Lisboa 2026',
  description: 'WC em tempo real · Rock in Rio Lisboa 2026',
  manifest: '/manifest.json',
  appleWebApp: { capable: true, statusBarStyle: 'default', title: 'PlantaOS' },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt">
      <body>
        <WSProvider>
          <Nav />
          <main className="page-enter">
            {children}
          </main>
        </WSProvider>
      </body>
    </html>
  )
}
