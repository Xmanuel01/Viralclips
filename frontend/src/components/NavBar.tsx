'use client'

import { useState } from 'react'
import { User } from '@supabase/supabase-js'
import { useAuth } from '@/hooks/useAuth'
import { Menu, X, Zap, Crown, LogOut, Settings } from 'lucide-react'
import Link from 'next/link'

interface NavBarProps {
  user: User
}

export function NavBar({ user }: NavBarProps) {
  const { signOut } = useAuth()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const handleSignOut = async () => {
    await signOut()
    setIsMenuOpen(false)
  }

  return (
    <nav className="bg-white/10 backdrop-blur-sm border-b border-white/20">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <Zap className="w-8 h-8 text-primary-400" />
            <span className="text-xl font-bold gradient-text">ViralClips.ai</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <Link 
              href="/dashboard" 
              className="text-white/70 hover:text-white transition-colors"
            >
              Dashboard
            </Link>
            <Link 
              href="/pricing" 
              className="text-white/70 hover:text-white transition-colors flex items-center"
            >
              <Crown className="w-4 h-4 mr-1" />
              Pricing
            </Link>
            
            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex items-center space-x-2 text-white/70 hover:text-white transition-colors"
              >
                <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium">
                    {user.email?.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="hidden lg:block">{user.email}</span>
              </button>

              {/* Dropdown Menu */}
              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg shadow-lg z-50">
                  <div className="py-1">
                    <Link
                      href="/account"
                      className="flex items-center px-4 py-2 text-white/70 hover:text-white hover:bg-white/10 transition-colors"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Account
                    </Link>
                    <Link
                      href="/pricing"
                      className="flex items-center px-4 py-2 text-white/70 hover:text-white hover:bg-white/10 transition-colors"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      <Crown className="w-4 h-4 mr-2" />
                      Upgrade
                    </Link>
                    <button
                      onClick={handleSignOut}
                      className="flex items-center w-full px-4 py-2 text-white/70 hover:text-white hover:bg-white/10 transition-colors"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden text-white/70 hover:text-white transition-colors"
          >
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-white/20 py-4">
            <div className="space-y-2">
              <Link
                href="/dashboard"
                className="block px-4 py-2 text-white/70 hover:text-white transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                Dashboard
              </Link>
              <Link
                href="/pricing"
                className="block px-4 py-2 text-white/70 hover:text-white transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                Pricing
              </Link>
              <Link
                href="/account"
                className="block px-4 py-2 text-white/70 hover:text-white transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                Account
              </Link>
              <button
                onClick={handleSignOut}
                className="block w-full text-left px-4 py-2 text-white/70 hover:text-white transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
