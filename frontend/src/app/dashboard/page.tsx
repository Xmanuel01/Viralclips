'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { NavBar } from '@/components/NavBar'
import { UploadArea } from '@/components/UploadArea'
import { VideoCard } from '@/components/VideoCard'
import { ClipCard } from '@/components/ClipCard'
import { UserStats } from '@/components/UserStats'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ApiClient } from '@/lib/api'
import { Video, Clip, UserStats as UserStatsType } from '@/types'
import { toast } from 'react-hot-toast'
import { Play, Upload, Zap, Download } from 'lucide-react'

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [videos, setVideos] = useState<Video[]>([])
  const [clips, setClips] = useState<Clip[]>([])
  const [stats, setStats] = useState<UserStatsType | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'upload' | 'videos' | 'clips'>('upload')

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth')
      return
    }

    if (user) {
      loadData()
    }
  }, [user, authLoading, router])

  const loadData = async () => {
    try {
      setLoading(true)
      const [videosRes, clipsRes, statsRes] = await Promise.all([
        ApiClient.getUserVideos(),
        ApiClient.getUserClips(),
        ApiClient.getUserStats()
      ])
      
      setVideos(videosRes.videos)
      setClips(clipsRes.clips)
      setStats(statsRes)
    } catch (error) {
      toast.error('Failed to load data')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleVideoProcessed = () => {
    loadData() // Refresh data when video is processed
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!user) {
    return null // Will redirect to auth
  }

  return (
    <div className="min-h-screen">
      <NavBar user={user} />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold gradient-text mb-4">
            Turn Long Videos into Viral Clips
          </h1>
          <p className="text-xl text-white/70 max-w-2xl mx-auto">
            Upload your videos or paste YouTube links. Our AI finds the best moments 
            and creates viral-ready clips for TikTok, Instagram Reels, and YouTube Shorts.
          </p>
        </div>

        {/* User Stats */}
        {stats && <UserStats stats={stats} className="mb-8" />}

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-1 flex space-x-1">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-6 py-2 rounded-md font-medium transition-all ${
                activeTab === 'upload'
                  ? 'bg-primary-600 text-white shadow-lg'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              <Upload className="w-4 h-4 inline mr-2" />
              Upload
            </button>
            <button
              onClick={() => setActiveTab('videos')}
              className={`px-6 py-2 rounded-md font-medium transition-all ${
                activeTab === 'videos'
                  ? 'bg-primary-600 text-white shadow-lg'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              <Play className="w-4 h-4 inline mr-2" />
              Videos ({videos.length})
            </button>
            <button
              onClick={() => setActiveTab('clips')}
              className={`px-6 py-2 rounded-md font-medium transition-all ${
                activeTab === 'clips'
                  ? 'bg-primary-600 text-white shadow-lg'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              <Zap className="w-4 h-4 inline mr-2" />
              Clips ({clips.length})
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-6xl mx-auto">
          {activeTab === 'upload' && (
            <div className="space-y-8">
              <UploadArea onVideoProcessed={handleVideoProcessed} />
              
              {/* Recent Videos */}
              {videos.length > 0 && (
                <div>
                  <h2 className="text-2xl font-bold text-white mb-6">Recent Videos</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {videos.slice(0, 3).map((video) => (
                      <VideoCard 
                        key={video.id} 
                        video={video} 
                        onUpdate={handleVideoProcessed}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'videos' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Your Videos</h2>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="btn-primary"
                >
                  <Upload className="w-4 h-4 inline mr-2" />
                  Upload New Video
                </button>
              </div>
              
              {videos.length === 0 ? (
                <div className="card text-center py-12">
                  <Upload className="w-16 h-16 text-white/50 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">No videos yet</h3>
                  <p className="text-white/70 mb-6">Upload your first video to get started</p>
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="btn-primary"
                  >
                    Upload Video
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {videos.map((video) => (
                    <VideoCard 
                      key={video.id} 
                      video={video} 
                      onUpdate={handleVideoProcessed}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'clips' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Your Clips</h2>
                <div className="text-white/70">
                  {stats && `${stats.clips_used_today}/${stats.max_clips_per_day} clips used today`}
                </div>
              </div>
              
              {clips.length === 0 ? (
                <div className="card text-center py-12">
                  <Zap className="w-16 h-16 text-white/50 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">No clips yet</h3>
                  <p className="text-white/70 mb-6">Process a video to generate viral clips</p>
                  <button
                    onClick={() => setActiveTab('videos')}
                    className="btn-primary"
                  >
                    View Videos
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {clips.map((clip) => (
                    <ClipCard 
                      key={clip.id} 
                      clip={clip} 
                      onUpdate={handleVideoProcessed}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Features Section */}
        <div className="mt-20 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">
            How It Works
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Upload className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Upload or Link</h3>
              <p className="text-white/70">Upload video files or paste YouTube links</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-accent-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">AI Processing</h3>
              <p className="text-white/70">Our AI finds the most engaging moments</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Download className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Download & Share</h3>
              <p className="text-white/70">Get viral-ready clips for all platforms</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
