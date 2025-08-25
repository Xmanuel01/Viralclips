'use client'

import { useContext } from 'react'
import { createContext } from 'react'
import { User } from '@supabase/supabase-js'

interface AuthContextType {
  user: User | null
  loading: boolean
  signOut: () => Promise<void>
}

// Re-export the context from AuthProvider for convenience
export { useAuth } from '@/components/AuthProvider'
