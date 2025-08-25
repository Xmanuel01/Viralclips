'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { 
  Play,
  Zap, 
  Video, 
  Scissors, 
  Brain, 
  Download, 
  Share2,
  TrendingUp,
  Clock,
  Star,
  Check,
  ArrowRight,
  Youtube,
  Upload,
  Sparkles
} from 'lucide-react'

export default function HomePage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && user) {
      // Redirect authenticated users to dashboard
      router.push('/dashboard')
    }
  }, [user, authLoading, router])

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (user) {
    return null // Will redirect to dashboard
  }

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="container mx-auto px-4 py-20 text-center">
          <div className="flex items-center justify-center mb-6">
            <Zap className="w-12 h-12 text-primary-400 mr-3" />
            <span className="text-3xl font-bold gradient-text">ViralClips.ai</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Turn Long Videos Into
            <span className="block gradient-text">Viral Clips</span>
            <span className="block text-white">With AI</span>
          </h1>
          
          <p className="text-xl text-white/70 max-w-3xl mx-auto mb-8">
            Upload your podcast, webinar, or YouTube video and let our AI find the most 
            engaging moments. Export perfect clips for TikTok, Instagram, and YouTube Shorts.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <a
              href="/auth"
              className="btn-primary text-lg px-8 py-4 flex items-center"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Start Creating Free
            </a>
            <a
              href="/pricing"
              className="btn-secondary text-lg px-8 py-4 flex items-center"
            >
              <TrendingUp className="w-5 h-5 mr-2" />
              View Pricing
            </a>
          </div>
          
          <div className="flex items-center justify-center text-white/60 text-sm">
            <Check className="w-4 h-4 mr-2 text-green-400" />
            Free forever • No credit card required • 3 clips daily
          </div>
        </div>
        
        {/* Animated background */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary-500/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-accent-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-white/5">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-6">How It Works</h2>
            <p className="text-xl text-white/70 max-w-2xl mx-auto">
              Three simple steps to viral content
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="card text-center">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Upload className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">1. Upload Your Video</h3>
              <p className="text-white/70">
                Drop a video file or paste a YouTube link. We support all major formats up to 1GB.
              </p>
            </div>
            
            <div className="card text-center">
              <div className="w-16 h-16 bg-accent-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">2. AI Finds Highlights</h3>
              <p className="text-white/70">
                Our AI analyzes your content for engaging moments, viral keywords, and perfect cuts.
              </p>
            </div>
            
            <div className="card text-center">
              <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Download className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">3. Export & Share</h3>
              <p className="text-white/70">
                Download HD clips optimized for every platform. TikTok, Instagram, YouTube - we've got you covered.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-6">Powered by AI</h2>
            <p className="text-xl text-white/70 max-w-2xl mx-auto">
              Advanced technology that understands what makes content go viral
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="flex items-start">
                <div className="w-12 h-12 bg-primary-600/20 rounded-lg flex items-center justify-center mr-4 mt-1">
                  <Scissors className="w-6 h-6 text-primary-400" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Smart Scene Detection</h3>
                  <p className="text-white/70">
                    Automatically identifies scene changes, speaker transitions, and natural break points.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="w-12 h-12 bg-accent-600/20 rounded-lg flex items-center justify-center mr-4 mt-1">
                  <Brain className="w-6 h-6 text-accent-400" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Viral Content Analysis</h3>
                  <p className="text-white/70">
                    AI trained on millions of viral videos to identify engaging moments and trending topics.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="w-12 h-12 bg-green-600/20 rounded-lg flex items-center justify-center mr-4 mt-1">
                  <Share2 className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Multi-Platform Export</h3>
                  <p className="text-white/70">
                    Perfect aspect ratios and formats for TikTok (9:16), Instagram (1:1), and YouTube (16:9).
                  </p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="w-12 h-12 bg-yellow-600/20 rounded-lg flex items-center justify-center mr-4 mt-1">
                  <Clock className="w-6 h-6 text-yellow-400" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Lightning Fast</h3>
                  <p className="text-white/70">
                    Process hours of content in minutes. Get your viral clips while they're still trending.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="relative">
              <div className="card bg-gradient-to-br from-primary-500/10 to-accent-500/10 p-8">
                <div className="space-y-6">
                  <div className="flex items-center">
                    <Youtube className="w-8 h-8 text-red-500 mr-3" />
                    <div className="flex-1">
                      <div className="h-2 bg-white/10 rounded-full">
                        <div className="h-2 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full w-3/4"></div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-center text-white/80 text-sm">
                    Processing: "2-Hour Podcast Episode"
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-white/5 p-3 rounded-lg">
                      <Video className="w-6 h-6 text-primary-400 mb-2" />
                      <div className="text-xs text-white/60">Clip 1 (0:45)</div>
                      <div className="text-sm text-white">"Best Moment"</div>
                    </div>
                    <div className="bg-white/5 p-3 rounded-lg">
                      <Video className="w-6 h-6 text-accent-400 mb-2" />
                      <div className="text-xs text-white/60">Clip 2 (1:20)</div>
                      <div className="text-sm text-white">"Viral Quote"</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-center">
                    <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm">
                      <Check className="w-4 h-4 inline mr-1" />
                      Ready to export!
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-20 bg-white/5">
        <div className="container mx-auto px-4 text-center">
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Trusted by Content Creators</h2>
            <p className="text-white/70">Join thousands of creators who've gone viral with ViralClips.ai</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-400 mb-2">10K+</div>
              <div className="text-white/70">Videos Processed</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-accent-400 mb-2">50K+</div>
              <div className="text-white/70">Clips Generated</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400 mb-2">5M+</div>
              <div className="text-white/70">Views Generated</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400 mb-2">2K+</div>
              <div className="text-white/70">Happy Creators</div>
            </div>
          </div>
          
          <div className="flex items-center justify-center mb-8">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className="w-6 h-6 text-yellow-400 fill-current" />
            ))}
            <span className="ml-3 text-white font-medium">4.9/5 from 200+ reviews</span>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to Go Viral?
            </h2>
            <p className="text-xl text-white/70 mb-8 max-w-2xl mx-auto">
              Start creating viral clips from your content today. 
              No technical skills required, just upload and watch the magic happen.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
              <a
                href="/auth"
                className="btn-primary text-lg px-8 py-4 flex items-center"
              >
                <Play className="w-5 h-5 mr-2" />
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </a>
              <a
                href="/pricing"
                className="btn-secondary text-lg px-8 py-4"
              >
                View Pricing Plans
              </a>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-white/60 max-w-2xl mx-auto">
              <div className="flex items-center justify-center">
                <Check className="w-4 h-4 mr-2 text-green-400" />
                3 free clips daily
              </div>
              <div className="flex items-center justify-center">
                <Check className="w-4 h-4 mr-2 text-green-400" />
                No credit card required
              </div>
              <div className="flex items-center justify-center">
                <Check className="w-4 h-4 mr-2 text-green-400" />
                Cancel anytime
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/10">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <Zap className="w-8 h-8 text-primary-400 mr-2" />
              <span className="text-xl font-bold gradient-text">ViralClips.ai</span>
            </div>
            
            <div className="flex items-center space-x-6 text-white/60">
              <a href="/pricing" className="hover:text-white transition-colors">Pricing</a>
              <a href="/docs" className="hover:text-white transition-colors">Docs</a>
              <a href="mailto:support@viralclips.ai" className="hover:text-white transition-colors">Support</a>
              <a href="/privacy" className="hover:text-white transition-colors">Privacy</a>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-white/10 text-center text-white/60 text-sm">
            © 2024 ViralClips.ai. All rights reserved. Made with ❤️ for content creators.
          </div>
        </div>
      </footer>
    </div>
  )
}
