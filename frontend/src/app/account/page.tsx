'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { usePaystack } from '@/lib/paystack'
import { NavBar } from '@/components/NavBar'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { toast } from 'react-hot-toast'
import { supabase } from '@/lib/supabase'
import { 
  User,
  Crown, 
  CreditCard,
  Calendar,
  Settings,
  Shield,
  LogOut,
  Edit3,
  Mail,
  Phone,
  MapPin,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  AlertTriangle,
  ExternalLink
} from 'lucide-react'

interface UserProfile {
  id: string
  email: string
  full_name?: string
  phone?: string
  subscription_tier: 'free' | 'premium' | 'lifetime'
  subscription_status: 'active' | 'inactive' | 'cancelled'
  subscription_expires_at?: string
  created_at: string
  total_videos: number
  total_clips: number
  clips_used_today: number
}

export default function AccountPage() {
  const { user, loading: authLoading, signOut } = useAuth()
  const { openPaymentModal, verifyPayment, formatCurrency } = usePaystack()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    full_name: '',
    phone: ''
  })

  useEffect(() => {
    if (user) {
      fetchProfile()
    }
  }, [user])

  const fetchProfile = async () => {
    if (!user) return

    try {
      setLoading(true)
      
      // Mock profile data - in real app this would come from your API
      const mockProfile: UserProfile = {
        id: user.id,
        email: user.email!,
        full_name: user.user_metadata?.full_name || '',
        phone: user.user_metadata?.phone || '',
        subscription_tier: 'free', // This would come from your database
        subscription_status: 'active',
        subscription_expires_at: undefined,
        created_at: user.created_at,
        total_videos: 5,
        total_clips: 12,
        clips_used_today: 2
      }
      
      setProfile(mockProfile)
      setEditForm({
        full_name: mockProfile.full_name || '',
        phone: mockProfile.phone || ''
      })
    } catch (error) {
      console.error('Error fetching profile:', error)
      toast.error('Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveProfile = async () => {
    if (!user) return

    try {
      setIsProcessing(true)
      
      const { error } = await supabase.auth.updateUser({
        data: {
          full_name: editForm.full_name,
          phone: editForm.phone
        }
      })

      if (error) throw error

      setProfile(prev => prev ? {
        ...prev,
        full_name: editForm.full_name,
        phone: editForm.phone
      } : null)

      setIsEditing(false)
      toast.success('Profile updated successfully')
    } catch (error) {
      console.error('Error updating profile:', error)
      toast.error('Failed to update profile')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleUpgrade = async (planType: 'premium' | 'lifetime') => {
    if (!user) return

    try {
      setIsProcessing(true)

      await openPaymentModal(
        user.email!,
        planType,
        user.id,
        async (reference: string) => {
          try {
            const result = await verifyPayment(reference)
            toast.success('Payment successful! Your subscription has been upgraded.')
            fetchProfile() // Refresh profile
          } catch (error) {
            toast.error('Payment verification failed')
            console.error(error)
          }
        },
        () => {
          setIsProcessing(false)
        }
      )
    } catch (error) {
      toast.error('Failed to process payment')
      console.error(error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSignOut = async () => {
    try {
      await signOut()
      toast.success('Signed out successfully')
    } catch (error) {
      toast.error('Failed to sign out')
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!user || !profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-white/70 mb-4">Please sign in to access your account</p>
          <a href="/auth" className="btn-primary">
            Sign In
          </a>
        </div>
      </div>
    )
  }

  const getDailyLimit = () => {
    switch (profile.subscription_tier) {
      case 'premium':
      case 'lifetime':
        return 20
      default:
        return 3
    }
  }

  const getSubscriptionBadge = () => {
    const tier = profile.subscription_tier
    const status = profile.subscription_status

    if (tier === 'lifetime') {
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-accent-600 text-white">
          <Crown className="w-4 h-4 mr-1" />
          Lifetime
        </span>
      )
    }

    if (tier === 'premium') {
      return (
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
          status === 'active' 
            ? 'bg-primary-600 text-white' 
            : 'bg-red-600 text-white'
        }`}>
          <Crown className="w-4 h-4 mr-1" />
          Premium {status !== 'active' && `(${status})`}
        </span>
      )
    }

    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-600 text-white">
        Free
      </span>
    )
  }

  return (
    <div className="min-h-screen">
      <NavBar user={user} />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Account Settings</h1>
          <p className="text-white/70">Manage your profile, subscription, and billing</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Profile Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Profile Info */}
            <div className="card">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-white">Profile Information</h2>
                {!isEditing ? (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="btn-secondary"
                  >
                    <Edit3 className="w-4 h-4 mr-2" />
                    Edit
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="btn-secondary"
                      disabled={isProcessing}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveProfile}
                      className="btn-primary"
                      disabled={isProcessing}
                    >
                      {isProcessing ? <LoadingSpinner size="sm" /> : 'Save'}
                    </button>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div className="flex items-center">
                  <Mail className="w-5 h-5 text-white/60 mr-3" />
                  <div>
                    <label className="text-sm text-white/60">Email</label>
                    <p className="text-white">{profile.email}</p>
                  </div>
                </div>

                <div className="flex items-center">
                  <User className="w-5 h-5 text-white/60 mr-3" />
                  <div className="flex-1">
                    <label className="text-sm text-white/60">Full Name</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editForm.full_name}
                        onChange={(e) => setEditForm(prev => ({ ...prev, full_name: e.target.value }))}
                        className="block w-full mt-1 px-3 py-2 bg-white/5 border border-white/10 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Enter your full name"
                      />
                    ) : (
                      <p className="text-white">{profile.full_name || 'Not provided'}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center">
                  <Phone className="w-5 h-5 text-white/60 mr-3" />
                  <div className="flex-1">
                    <label className="text-sm text-white/60">Phone</label>
                    {isEditing ? (
                      <input
                        type="tel"
                        value={editForm.phone}
                        onChange={(e) => setEditForm(prev => ({ ...prev, phone: e.target.value }))}
                        className="block w-full mt-1 px-3 py-2 bg-white/5 border border-white/10 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Enter your phone number"
                      />
                    ) : (
                      <p className="text-white">{profile.phone || 'Not provided'}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center">
                  <Calendar className="w-5 h-5 text-white/60 mr-3" />
                  <div>
                    <label className="text-sm text-white/60">Member Since</label>
                    <p className="text-white">
                      {new Date(profile.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Usage Stats */}
            <div className="card">
              <h2 className="text-xl font-semibold text-white mb-6">Usage Statistics</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white/5 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-primary-400 mb-1">
                    {profile.total_videos}
                  </div>
                  <div className="text-sm text-white/70">Videos Uploaded</div>
                </div>
                
                <div className="bg-white/5 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-accent-400 mb-1">
                    {profile.total_clips}
                  </div>
                  <div className="text-sm text-white/70">Clips Generated</div>
                </div>
                
                <div className="bg-white/5 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-400 mb-1">
                    {profile.clips_used_today}/{getDailyLimit()}
                  </div>
                  <div className="text-sm text-white/70">Today's Usage</div>
                </div>
              </div>

              {/* Usage Progress */}
              <div className="mt-6">
                <div className="flex justify-between text-sm text-white/70 mb-2">
                  <span>Daily Clip Limit</span>
                  <span>{profile.clips_used_today} / {getDailyLimit()}</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div 
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${Math.min((profile.clips_used_today / getDailyLimit()) * 100, 100)}%` 
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Security */}
            <div className="card">
              <h2 className="text-xl font-semibold text-white mb-6">Security</h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-medium">Password</h3>
                    <p className="text-sm text-white/70">Last updated 30 days ago</p>
                  </div>
                  <button className="btn-secondary">
                    Change Password
                  </button>
                </div>

                <div className="border-t border-white/10 pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-red-400 font-medium">Sign Out</h3>
                      <p className="text-sm text-white/70">Sign out from this device</p>
                    </div>
                    <button 
                      onClick={handleSignOut}
                      className="btn-secondary text-red-400 hover:bg-red-600/10"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Subscription Sidebar */}
          <div className="space-y-6">
            {/* Current Plan */}
            <div className="card">
              <h2 className="text-xl font-semibold text-white mb-4">Current Plan</h2>
              
              <div className="text-center mb-6">
                {getSubscriptionBadge()}
                
                <div className="mt-4">
                  {profile.subscription_tier === 'free' ? (
                    <div className="text-2xl font-bold text-white">Free</div>
                  ) : profile.subscription_tier === 'lifetime' ? (
                    <div className="text-2xl font-bold text-accent-400">
                      {formatCurrency(99)} <span className="text-sm font-normal">lifetime</span>
                    </div>
                  ) : (
                    <div className="text-2xl font-bold text-primary-400">
                      {formatCurrency(15)} <span className="text-sm font-normal">/month</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/70">Daily Clips</span>
                  <span className="text-white font-medium">{getDailyLimit()}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/70">Export Quality</span>
                  <span className="text-white font-medium">
                    {profile.subscription_tier === 'free' ? '720p' : '1080p'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/70">Watermark</span>
                  <span className="text-white font-medium">
                    {profile.subscription_tier === 'free' ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/70">Support</span>
                  <span className="text-white font-medium">
                    {profile.subscription_tier === 'free' 
                      ? 'Community' 
                      : profile.subscription_tier === 'lifetime'
                        ? 'Priority'
                        : 'Email'
                    }
                  </span>
                </div>
              </div>

              {profile.subscription_tier === 'free' && (
                <div className="space-y-2">
                  <button 
                    onClick={() => handleUpgrade('premium')}
                    disabled={isProcessing}
                    className="btn-primary w-full"
                  >
                    <Crown className="w-4 h-4 mr-2" />
                    Upgrade to Premium
                  </button>
                  <button 
                    onClick={() => handleUpgrade('lifetime')}
                    disabled={isProcessing}
                    className="btn-accent w-full"
                  >
                    <Crown className="w-4 h-4 mr-2" />
                    Get Lifetime Access
                  </button>
                </div>
              )}

              {profile.subscription_tier === 'premium' && (
                <>
                  {profile.subscription_expires_at && (
                    <div className="bg-white/5 p-3 rounded-lg mb-4">
                      <div className="flex items-center text-sm">
                        <Clock className="w-4 h-4 text-white/60 mr-2" />
                        <span className="text-white/70">
                          Renews {new Date(profile.subscription_expires_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  )}
                  <button 
                    onClick={() => handleUpgrade('lifetime')}
                    disabled={isProcessing}
                    className="btn-accent w-full"
                  >
                    <Crown className="w-4 h-4 mr-2" />
                    Upgrade to Lifetime
                  </button>
                </>
              )}
            </div>

            {/* Billing History */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">Billing History</h2>
                <button className="text-primary-400 hover:text-primary-300 text-sm">
                  <ExternalLink className="w-4 h-4 inline mr-1" />
                  View All
                </button>
              </div>
              
              <div className="space-y-3">
                {profile.subscription_tier === 'free' ? (
                  <p className="text-white/60 text-sm text-center py-4">
                    No billing history yet
                  </p>
                ) : (
                  <div className="bg-white/5 p-3 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white font-medium">
                          {profile.subscription_tier === 'lifetime' ? 'Lifetime Access' : 'Premium Monthly'}
                        </div>
                        <div className="text-sm text-white/60">
                          {new Date().toLocaleDateString()}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-medium">
                          {formatCurrency(profile.subscription_tier === 'lifetime' ? 99 : 15)}
                        </div>
                        <div className="flex items-center text-sm text-green-400">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Paid
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Support */}
            <div className="card">
              <h2 className="text-xl font-semibold text-white mb-4">Need Help?</h2>
              
              <div className="space-y-3">
                <a 
                  href="/docs" 
                  className="block p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <div className="text-white font-medium">Documentation</div>
                  <div className="text-sm text-white/60">Learn how to use ViralClips.ai</div>
                </a>
                
                <a 
                  href="mailto:support@viralclips.ai" 
                  className="block p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <div className="text-white font-medium">Email Support</div>
                  <div className="text-sm text-white/60">Get help from our team</div>
                </a>
                
                <a 
                  href="/pricing" 
                  className="block p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <div className="text-white font-medium">Upgrade Plan</div>
                  <div className="text-sm text-white/60">Get more features and support</div>
                </a>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
