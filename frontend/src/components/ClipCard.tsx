'use client'

import { useState } from 'react'
import { Clip, ExportFormat, JobStatus } from '@/types'
import { ApiClient, formatFileSize } from '@/lib/api'
import { toast } from 'react-hot-toast'
import { Download, Play, Clock, Loader2, AlertCircle, CheckCircle, Eye } from 'lucide-react'

interface ClipCardProps {
  clip: Clip
  onUpdate: () => void
}

export function ClipCard({ clip, onUpdate }: ClipCardProps) {
  const [isDownloading, setIsDownloading] = useState(false)

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

  const getFormatIcon = (format: ExportFormat) => {
    switch (format) {
      case ExportFormat.VERTICAL:
        return '📱'
      case ExportFormat.SQUARE:
        return '⬜'
      case ExportFormat.HORIZONTAL:
        return '📺'
      default:
        return '🎬'
    }
  }

  const getFormatLabel = (format: ExportFormat) => {
    switch (format) {
      case ExportFormat.VERTICAL:
        return 'Vertical (9:16)'
      case ExportFormat.SQUARE:
        return 'Square (1:1)'
      case ExportFormat.HORIZONTAL:
        return 'Horizontal (16:9)'
      default:
        return format
    }
  }

  const handleDownload = async () => {
    try {
      setIsDownloading(true)
      const response = await ApiClient.getClipDownloadUrl(clip.id)
      
      // Create download link
      const link = document.createElement('a')
      link.href = response.download_url
      link.download = `${clip.title}.mp4`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      toast.success('Download started')
    } catch (error) {
      toast.error('Failed to download clip')
    } finally {
      setIsDownloading(false)
    }
  }

  const handlePreview = () => {
    // TODO: Implement video preview modal
    toast('Preview feature coming soon!', { icon: 'ℹ️' })
  }

  return (
    <div className="clip-card">
      {/* Clip Info */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-2 line-clamp-2">
            {clip.title}
          </h3>
          
          <div className="flex items-center space-x-3 text-sm text-white/60">
            <span className="flex items-center">
              {getFormatIcon(clip.export_format as ExportFormat)}
              <span className="ml-1">{getFormatLabel(clip.export_format as ExportFormat)}</span>
            </span>
            <span>{clip.resolution}</span>
            {clip.has_watermark && (
              <span className="text-yellow-400">Watermarked</span>
            )}
          </div>
        </div>

        {/* Status */}
        <div className={`flex items-center space-x-1 ${getStatusColor(clip.status as JobStatus)}`}>
          {getStatusIcon(clip.status as JobStatus)}
          <span className="text-xs capitalize">{clip.status}</span>
        </div>
      </div>

      {/* Thumbnail/Preview */}
      <div className="bg-white/5 rounded-lg aspect-video flex items-center justify-center mb-4 relative">
        <Play className="w-12 h-12 text-white/50" />
        
        {/* Format Indicator */}
        <div className="absolute top-2 left-2 bg-black/50 rounded px-2 py-1 text-xs text-white">
          {getFormatIcon(clip.export_format as ExportFormat)} {clip.export_format}
        </div>
      </div>

      {/* File Info */}
      {clip.file_size > 0 && (
        <div className="text-sm text-white/60 mb-4">
          File size: {formatFileSize(clip.file_size)}
        </div>
      )}

      {/* Actions */}
      <div className="flex space-x-2">
        {clip.status === JobStatus.COMPLETED && (
          <>
            <button
              onClick={handlePreview}
              className="btn-secondary flex-1 text-sm"
            >
              <Eye className="w-4 h-4 inline mr-1" />
              Preview
            </button>
            
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="btn-primary flex-1 text-sm disabled:opacity-50"
            >
              {isDownloading ? (
                <Loader2 className="w-4 h-4 inline mr-1 animate-spin" />
              ) : (
                <Download className="w-4 h-4 inline mr-1" />
              )}
              Download
            </button>
          </>
        )}

        {clip.status === JobStatus.PROCESSING && (
          <div className="flex-1 text-center py-2">
            <span className="text-white/70 text-sm">Generating clip...</span>
          </div>
        )}

        {clip.status === JobStatus.FAILED && (
          <div className="flex-1 text-center py-2">
            <span className="text-red-400 text-sm">Generation failed</span>
          </div>
        )}

        {clip.status === JobStatus.PENDING && (
          <div className="flex-1 text-center py-2">
            <span className="text-white/70 text-sm">Pending...</span>
          </div>
        )}
      </div>

      {/* Creation Date */}
      <div className="mt-3 pt-3 border-t border-white/10 text-xs text-white/50">
        Created {new Date(clip.created_at).toLocaleDateString()}
      </div>
    </div>
  )
}
