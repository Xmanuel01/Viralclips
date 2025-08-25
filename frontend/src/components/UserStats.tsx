'use client'

import { UserStats as UserStatsType, SubscriptionTier } from '@/types'
import { Crown, Zap, Clock } from 'lucide-react'
import Link from 'next/link'

interface UserStatsProps {
  stats: UserStatsType
  className?: string
}

export function UserStats({ stats, className = '' }: UserStatsProps) {
  const getTierColor = (tier: SubscriptionTier) => {
    switch (tier) {
      case SubscriptionTier.PREMIUM:
        return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20'
      case SubscriptionTier.LIFETIME:
        return 'text-purple-400 bg-purple-400/10 border-purple-400/20'
      default:
        return 'text-gray-400 bg-gray-400/10 border-gray-400/20'
    }
  }

  const getTierIcon = (tier: SubscriptionTier) => {
    switch (tier) {
      case SubscriptionTier.PREMIUM:
      case SubscriptionTier.LIFETIME:
        return <Crown className="w-4 h-4" />
      default:
        return null
    }
  }

  const progressPercentage = (stats.clips_used_today / stats.max_clips_per_day) * 100

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Subscription Tier */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium">Subscription</h3>
            {getTierIcon(stats.subscription_tier)}
          </div>
          
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getTierColor(stats.subscription_tier)}`}>
            {stats.subscription_tier === SubscriptionTier.FREE && 'Free Plan'}
            {stats.subscription_tier === SubscriptionTier.PREMIUM && 'Premium'}
            {stats.subscription_tier === SubscriptionTier.LIFETIME && 'Lifetime'}
          </div>
          
          {stats.subscription_tier === SubscriptionTier.FREE && (
            <div className="mt-3">
              <Link href="/pricing" className="text-primary-400 hover:text-primary-300 text-sm font-medium">
                Upgrade to Premium →
              </Link>
            </div>
          )}
        </div>

        {/* Daily Usage */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium">Daily Usage</h3>
            <Zap className="w-4 h-4 text-accent-400" />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-white/70">Clips used</span>
              <span className="text-white">{stats.clips_used_today} / {stats.max_clips_per_day}</span>
            </div>
            
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${Math.min(progressPercentage, 100)}%` }}
              />
            </div>
            
            <div className="text-sm text-white/60">
              {stats.clips_remaining} clips remaining today
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium">Quick Actions</h3>
            <Clock className="w-4 h-4 text-green-400" />
          </div>
          
          <div className="space-y-2">
            <Link 
              href="/pricing" 
              className="block text-sm text-primary-400 hover:text-primary-300 transition-colors"
            >
              View Pricing Plans
            </Link>
            <Link 
              href="/settings" 
              className="block text-sm text-white/70 hover:text-white transition-colors"
            >
              Account Settings
            </Link>
            <Link 
              href="/help" 
              className="block text-sm text-white/70 hover:text-white transition-colors"
            >
              Help & Support
            </Link>
          </div>
        </div>
      </div>

      {/* Usage Warning */}
      {stats.clips_remaining <= 1 && stats.subscription_tier === SubscriptionTier.FREE && (
        <div className="mt-6 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-yellow-400 rounded-full mr-3" />
            <div className="flex-1">
              <p className="text-yellow-200 font-medium">Almost at your daily limit!</p>
              <p className="text-yellow-200/70 text-sm">
                {stats.clips_remaining > 0 
                  ? `You have ${stats.clips_remaining} clip${stats.clips_remaining === 1 ? '' : 's'} remaining today.`
                  : 'You\'ve reached your daily limit. Upgrade for unlimited clips!'
                }
              </p>
            </div>
            {stats.clips_remaining === 0 && (
              <Link href="/pricing" className="btn-accent ml-4">
                Upgrade Now
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
