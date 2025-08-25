'use client'

import { useState } from 'react'
import { Video, JobStatus } from '@/types'
import { ApiClient, formatDuration, formatFileSize } from '@/lib/api'
import { toast } from 'react-hot-toast'
import { Play, Clock, FileText, Zap, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import Link from 'next/link'

interface VideoCardProps {
  video: Video
  onUpdate: () => void
}

export function VideoCard({ video, onUpdate }: VideoCardProps) {
  const [isProcessing, setIsProcessing] = useState(false)

  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case JobStatus.COMPLETED:
        return 'text-green-400'
      case JobStatus.PROCESSING:
        return 'text-yellow-400'
      case JobStatus.FAILED:
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case JobStatus.COMPLETED:
        return <CheckCircle className="w-4 h-4" />
      case JobStatus.PROCESSING:
        return <Loader2 className="w-4 h-4 animate-spin" />
      case JobStatus.FAILED:
        return <AlertCircle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  const handleTranscribe = async () => {
    try {
      setIsProcessing(true)
      const response = await ApiClient.transcribeVideo({ video_id: video.id })
      toast.success('Transcription started')
      onUpdate()
    } catch (error) {
      toast.error('Failed to start transcription')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleHighlight = async () => {
    try {
      setIsProcessing(true)
      const response = await ApiClient.detectHighlights({ 
        video_id: video.id, 
        max_highlights: 5 
      })
      toast.success('Highlight detection started')
      onUpdate()
    } catch (error) {
      toast.error('Failed to start highlight detection')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="video-card">
      {/* Video Info */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-2 line-clamp-2">
            {video.title}
          </h3>
          
          <div className="flex items-center space-x-4 text-sm text-white/60 mb-3">
            <span className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              {formatDuration(video.duration)}
            </span>
            <span>{formatFileSize(video.file_size)}</span>
            <span className="capitalize">{video.source}</span>
          </div>
        </div>

        {/* Status */}
        <div className={`flex items-center space-x-1 ${getStatusColor(video.status as JobStatus)}`}>
          {getStatusIcon(video.status as JobStatus)}
          <span className="text-xs capitalize">{video.status}</span>
        </div>
      </div>

      {/* Thumbnail/Preview */}
      <div className="bg-white/5 rounded-lg aspect-video flex items-center justify-center mb-4">
        <Play className="w-12 h-12 text-white/50" />
      </div>

      {/* Actions */}
      <div className="flex space-x-2">
        {video.status === JobStatus.COMPLETED && (
          <>
            <button
              onClick={handleTranscribe}
              disabled={isProcessing}
              className="btn-secondary flex-1 text-sm disabled:opacity-50"
            >
              <FileText className="w-4 h-4 inline mr-1" />
              Transcribe
            </button>
            
            <button
              onClick={handleHighlight}
              disabled={isProcessing}
              className="btn-primary flex-1 text-sm disabled:opacity-50"
            >
              <Zap className="w-4 h-4 inline mr-1" />
              Find Highlights
            </button>
          </>
        )}

        {video.status === JobStatus.PROCESSING && (
          <div className="flex-1 text-center py-2">
            <span className="text-white/70 text-sm">Processing...</span>
          </div>
        )}

        {video.status === JobStatus.FAILED && (
          <div className="flex-1 text-center py-2">
            <span className="text-red-400 text-sm">Processing failed</span>
          </div>
        )}

        {video.status === JobStatus.PENDING && (
          <div className="flex-1 text-center py-2">
            <span className="text-white/70 text-sm">Pending...</span>
          </div>
        )}
      </div>

      {/* View Details Link */}
      {video.status === JobStatus.COMPLETED && (
        <div className="mt-3 pt-3 border-t border-white/10">
          <Link
            href={`/video/${video.id}`}
            className="text-primary-400 hover:text-primary-300 text-sm font-medium transition-colors"
          >
            View Details & Highlights →
          </Link>
        </div>
      )}
    </div>
  )
}
