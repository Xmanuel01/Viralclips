'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { usePaystack } from '@/lib/paystack'
import { NavBar } from '@/components/NavBar'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { toast } from 'react-hot-toast'
import { 
  Check, 
  Crown, 
  Zap, 
  Star, 
  Video, 
  Download, 
  Shield, 
  Clock,
  Infinity
} from 'lucide-react'

export default function PricingPage() {
  const { user, loading: authLoading } = useAuth()
  const { openPaymentModal, verifyPayment, formatCurrency } = usePaystack()
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingPlan, setProcessingPlan] = useState<string | null>(null)

  const handleUpgrade = async (planType: 'premium' | 'lifetime') => {
    if (!user) {
      toast.error('Please sign in to upgrade')
      return
    }

    try {
      setIsProcessing(true)
      setProcessingPlan(planType)

      await openPaymentModal(
        user.email!,
        planType,
        user.id,
        async (reference: string) => {
          try {
            // Verify payment
            const result = await verifyPayment(reference)
            toast.success('Payment successful! Your subscription has been upgraded.')
            
            // Refresh page to show updated subscription
            window.location.reload()
          } catch (error) {
            toast.error('Payment verification failed')
            console.error(error)
          }
        },
        () => {
          setIsProcessing(false)
          setProcessingPlan(null)
        }
      )
    } catch (error) {
      toast.error('Failed to process payment')
      console.error(error)
    } finally {
      setIsProcessing(false)
      setProcessingPlan(null)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {user && <NavBar user={user} />}
      
      <main className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold gradient-text mb-6">
            Choose Your Plan
          </h1>
          <p className="text-xl text-white/70 max-w-3xl mx-auto">
            Start for free, upgrade when you're ready to go viral. 
            All plans include AI-powered highlight detection and multi-platform exports.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Free Plan */}
          <div className="card relative">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gray-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Video className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Free</h3>
              <div className="text-3xl font-bold text-white mb-2">
                {formatCurrency(0)}
                <span className="text-lg font-normal text-white/60">/month</span>
              </div>
              <p className="text-white/70">Perfect for getting started</p>
            </div>

            <div className="space-y-4 mb-8">
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">3 viral clips per day</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">720p export quality</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">AI highlight detection</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">All aspect ratios</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">100MB file limit</span>
              </div>
              <div className="flex items-center text-yellow-400">
                <Shield className="w-5 h-5 mr-3" />
                <span>Watermarked videos</span>
              </div>
            </div>

            <button 
              disabled
              className="btn-secondary w-full opacity-50 cursor-not-allowed"
            >
              Current Plan
            </button>
          </div>

          {/* Premium Plan */}
          <div className="card relative border-2 border-primary-500 bg-primary-500/5">
            {/* Popular Badge */}
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <div className="bg-primary-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                Most Popular
              </div>
            </div>

            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Crown className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Premium</h3>
              <div className="text-3xl font-bold text-white mb-2">
                {formatCurrency(15)}
                <span className="text-lg font-normal text-white/60">/month</span>
              </div>
              <p className="text-white/70">For serious content creators</p>
            </div>

            <div className="space-y-4 mb-8">
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">20 viral clips per day</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">1080p HD export quality</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">No watermarks</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">Priority processing</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">1GB file limit</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">Batch export</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">Email support</span>
              </div>
            </div>

            <button 
              onClick={() => handleUpgrade('premium')}
              disabled={isProcessing}
              className="btn-primary w-full disabled:opacity-50"
            >
              {processingPlan === 'premium' ? (
                <LoadingSpinner size="sm" />
              ) : (
                <>
                  <Crown className="w-4 h-4 inline mr-2" />
                  Upgrade to Premium
                </>
              )}
            </button>
          </div>

          {/* Lifetime Plan */}
          <div className="card relative border-2 border-accent-500 bg-accent-500/5">
            {/* Best Value Badge */}
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <div className="bg-accent-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                Best Value
              </div>
            </div>

            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-accent-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Infinity className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Lifetime</h3>
              <div className="text-3xl font-bold text-white mb-2">
                {formatCurrency(99)}
                <span className="text-lg font-normal text-white/60"> once</span>
              </div>
              <p className="text-white/70">Save {formatCurrency(81)} per year!</p>
            </div>

            <div className="space-y-4 mb-8">
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">All Premium features</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">Lifetime access</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">Future updates included</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">Priority support</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 text-green-400 mr-3" />
                <span className="text-white/80">Commercial license</span>
              </div>
              <div className="flex items-center">
                <Star className="w-5 h-5 text-yellow-400 mr-3" />
                <span className="text-white/80">Early access to new features</span>
              </div>
            </div>

            <button 
              onClick={() => handleUpgrade('lifetime')}
              disabled={isProcessing}
              className="btn-accent w-full disabled:opacity-50"
            >
              {processingPlan === 'lifetime' ? (
                <LoadingSpinner size="sm" />
              ) : (
                <>
                  <Infinity className="w-4 h-4 inline mr-2" />
                  Get Lifetime Access
                </>
              )}
            </button>
          </div>
        </div>

        {/* Feature Comparison */}
        <div className="max-w-4xl mx-auto mt-20">
          <h2 className="text-3xl font-bold text-center text-white mb-12">
            Feature Comparison
          </h2>
          
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5">
                  <tr>
                    <th className="text-left py-4 px-6 text-white font-medium">Feature</th>
                    <th className="text-center py-4 px-6 text-white font-medium">Free</th>
                    <th className="text-center py-4 px-6 text-white font-medium">Premium</th>
                    <th className="text-center py-4 px-6 text-white font-medium">Lifetime</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  <tr>
                    <td className="py-4 px-6 text-white/80">Clips per day</td>
                    <td className="py-4 px-6 text-center text-white/60">3</td>
                    <td className="py-4 px-6 text-center text-primary-400">20</td>
                    <td className="py-4 px-6 text-center text-accent-400">20</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 text-white/80">Export quality</td>
                    <td className="py-4 px-6 text-center text-white/60">720p</td>
                    <td className="py-4 px-6 text-center text-primary-400">1080p</td>
                    <td className="py-4 px-6 text-center text-accent-400">1080p</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 text-white/80">Watermark</td>
                    <td className="py-4 px-6 text-center text-yellow-400">Yes</td>
                    <td className="py-4 px-6 text-center text-green-400">No</td>
                    <td className="py-4 px-6 text-center text-green-400">No</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 text-white/80">File size limit</td>
                    <td className="py-4 px-6 text-center text-white/60">100MB</td>
                    <td className="py-4 px-6 text-center text-primary-400">1GB</td>
                    <td className="py-4 px-6 text-center text-accent-400">1GB</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 text-white/80">Processing priority</td>
                    <td className="py-4 px-6 text-center text-white/60">Standard</td>
                    <td className="py-4 px-6 text-center text-primary-400">High</td>
                    <td className="py-4 px-6 text-center text-accent-400">Highest</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 text-white/80">Support</td>
                    <td className="py-4 px-6 text-center text-white/60">Community</td>
                    <td className="py-4 px-6 text-center text-primary-400">Email</td>
                    <td className="py-4 px-6 text-center text-accent-400">Priority</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="max-w-3xl mx-auto mt-20">
          <h2 className="text-3xl font-bold text-center text-white mb-12">
            Frequently Asked Questions
          </h2>
          
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-xl font-semibold text-white mb-3">
                How does the AI highlight detection work?
              </h3>
              <p className="text-white/70">
                Our AI analyzes your video's audio transcription, identifies engaging moments using 
                sentiment analysis and viral keyword detection, then combines this with visual scene 
                changes to find the most shareable clips.
              </p>
            </div>

            <div className="card">
              <h3 className="text-xl font-semibold text-white mb-3">
                What video formats are supported?
              </h3>
              <p className="text-white/70">
                We support all major video formats including MP4, AVI, MOV, MKV, WMV, FLV, WebM, 
                and M4V. You can also paste YouTube links for direct processing.
              </p>
            </div>

            <div className="card">
              <h3 className="text-xl font-semibold text-white mb-3">
                Can I cancel my subscription anytime?
              </h3>
              <p className="text-white/70">
                Yes! You can cancel your Premium subscription at any time. You'll keep access until 
                the end of your billing period. Lifetime purchases are non-refundable but never expire.
              </p>
            </div>

            <div className="card">
              <h3 className="text-xl font-semibold text-white mb-3">
                Do you offer refunds?
              </h3>
              <p className="text-white/70">
                We offer a 7-day money-back guarantee for Premium subscriptions. If you're not 
                satisfied, contact us within 7 days for a full refund.
              </p>
            </div>

            <div className="card">
              <h3 className="text-xl font-semibold text-white mb-3">
                Is my payment information secure?
              </h3>
              <p className="text-white/70">
                Absolutely! We use Paystack for secure payment processing. We never store your 
                payment information on our servers. All transactions are encrypted and PCI compliant.
              </p>
            </div>
          </div>
        </div>

        {/* Money Back Guarantee */}
        <div className="max-w-2xl mx-auto mt-16 text-center">
          <div className="card bg-green-500/10 border-green-500/20">
            <div className="flex items-center justify-center mb-4">
              <Shield className="w-12 h-12 text-green-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">
              7-Day Money-Back Guarantee
            </h3>
            <p className="text-white/70">
              Try Premium risk-free. If you're not completely satisfied, 
              we'll refund your money within 7 days, no questions asked.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        {!user && (
          <div className="text-center mt-16">
            <p className="text-white/70 mb-6">
              Ready to create viral content?
            </p>
            <a href="/auth" className="btn-primary inline-flex items-center">
              <Zap className="w-4 h-4 mr-2" />
              Get Started Free
            </a>
          </div>
        )}
      </main>
    </div>
  )
}
