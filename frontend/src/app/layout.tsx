import './globals.css'
import type { Metadata } from 'next'
import ClientLayout from './ClientLayout'
import { AuthProvider } from '@/components/AuthProvider'

export const metadata: Metadata = {
  title: 'ViralClips.ai - Turn Long Videos into Viral Clips',
  description: 'Automatically convert long videos into short, viral-ready clips for TikTok, Instagram Reels, and YouTube Shorts',
  keywords: 'video editing, viral clips, TikTok, Instagram Reels, YouTube Shorts, AI video editing',
  authors: [{ name: 'ViralClips Team' }],
  creator: 'ViralClips.ai',
  publisher: 'ViralClips.ai',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  icons: {
    icon: [
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' }
    ],
    shortcut: '/favicon.ico',
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' }
    ],
    other: [
      {
        rel: 'apple-touch-icon-precomposed',
        url: '/apple-touch-icon.png'
      }
    ]
  },
  manifest: '/site.webmanifest',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://viralclips.ai',
    title: 'ViralClips.ai - Turn Long Videos into Viral Clips',
    description: 'Automatically convert long videos into short, viral-ready clips for TikTok, Instagram Reels, and YouTube Shorts',
    siteName: 'ViralClips.ai',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ViralClips.ai - Turn Long Videos into Viral Clips',
    description: 'Automatically convert long videos into short, viral-ready clips for TikTok, Instagram Reels, and YouTube Shorts',
    creator: '@viralclipsai'
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#7c3aed' },
    { media: '(prefers-color-scheme: dark)', color: '#7c3aed' }
  ]
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <ClientLayout>
        <AuthProvider>
          {children}
        </AuthProvider>
      </ClientLayout>
    </html>
  )
}
