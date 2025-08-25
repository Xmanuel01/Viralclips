'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { ApiClient, pollJobStatus, formatFileSize } from '@/lib/api'
import { VideoSource, MAX_FILE_SIZE_FREE, MAX_FILE_SIZE_PREMIUM } from '@/types'
import { toast } from 'react-hot-toast'
import { Upload, Link as LinkIcon, Play, Loader2 } from 'lucide-react'

interface UploadAreaProps {
  onVideoProcessed: () => void
}

export function UploadArea({ onVideoProcessed }: UploadAreaProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [videoTitle, setVideoTitle] = useState('')
  const [uploadMode, setUploadMode] = useState<'file' | 'youtube'>('file')

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Validate file size (assuming free tier for now)
    const maxSize = MAX_FILE_SIZE_FREE
    if (file.size > maxSize) {
      toast.error(`File too large. Maximum size is ${formatFileSize(maxSize)}`)
      return
    }

    await handleFileUpload(file)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    },
    multiple: false,
    disabled: isUploading
  })

  const handleFileUpload = async (file: File) => {
    try {
      setIsUploading(true)
      setUploadProgress(10)

      // Create video record
      const uploadResponse = await ApiClient.uploadVideo({
        title: file.name,
        source: VideoSource.UPLOAD
      })

      setUploadProgress(30)

      // Upload file
      await ApiClient.uploadFile(uploadResponse.video_id, file)

      setUploadProgress(50)

      // Poll for completion
      toast.loading('Processing video...', { id: 'upload' })
      
      const finalStatus = await pollJobStatus(
        uploadResponse.job_id,
        (status) => {
          setUploadProgress(50 + (status.progress * 0.5))
        }
      )

      if (finalStatus.status === 'completed') {
        toast.success('Video uploaded and processed successfully!', { id: 'upload' })
        onVideoProcessed()
      } else {
        toast.error('Failed to process video', { id: 'upload' })
      }

    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Failed to upload video', { id: 'upload' })
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const handleYouTubeUpload = async () => {
    if (!youtubeUrl || !videoTitle) {
      toast.error('Please provide both YouTube URL and title')
      return
    }

    try {
      setIsUploading(true)
      setUploadProgress(10)

      // Create video record for YouTube
      const uploadResponse = await ApiClient.uploadVideo({
        title: videoTitle,
        source: VideoSource.YOUTUBE,
        source_url: youtubeUrl
      })

      setUploadProgress(30)

      // Poll for completion
      toast.loading('Downloading and processing video...', { id: 'youtube' })
      
      const finalStatus = await pollJobStatus(
        uploadResponse.job_id,
        (status) => {
          setUploadProgress(30 + (status.progress * 0.7))
        }
      )

      if (finalStatus.status === 'completed') {
        toast.success('YouTube video processed successfully!', { id: 'youtube' })
        setYoutubeUrl('')
        setVideoTitle('')
        onVideoProcessed()
      } else {
        toast.error('Failed to process YouTube video', { id: 'youtube' })
      }

    } catch (error) {
      console.error('YouTube upload error:', error)
      toast.error('Failed to process YouTube video', { id: 'youtube' })
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Upload Mode Toggle */}
      <div className="flex justify-center mb-6">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-1 flex">
          <button
            onClick={() => setUploadMode('file')}
            className={`px-6 py-2 rounded-md font-medium transition-all ${
              uploadMode === 'file'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            <Upload className="w-4 h-4 inline mr-2" />
            Upload File
          </button>
          <button
            onClick={() => setUploadMode('youtube')}
            className={`px-6 py-2 rounded-md font-medium transition-all ${
              uploadMode === 'youtube'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            <LinkIcon className="w-4 h-4 inline mr-2" />
            YouTube Link
          </button>
        </div>
      </div>

      {/* File Upload */}
      {uploadMode === 'file' && (
        <div
          {...getRootProps()}
          className={`upload-area ${isDragActive ? 'border-primary-400 bg-primary-400/10' : ''} ${
            isUploading ? 'pointer-events-none opacity-50' : ''
          }`}
        >
          <input {...getInputProps()} />
          
          {isUploading ? (
            <div className="space-y-4">
              <Loader2 className="w-12 h-12 text-primary-400 mx-auto animate-spin" />
              <div>
                <p className="text-white font-medium mb-2">Processing video...</p>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-white/70 text-sm mt-1">{uploadProgress}%</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <Upload className="w-16 h-16 text-white/50 mx-auto" />
              <div>
                <p className="text-xl font-semibold text-white mb-2">
                  {isDragActive ? 'Drop your video here' : 'Upload your video'}
                </p>
                <p className="text-white/70 mb-4">
                  Drag and drop a video file, or click to browse
                </p>
                <p className="text-white/60 text-sm">
                  Supports MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V
                  <br />
                  Max size: {formatFileSize(MAX_FILE_SIZE_FREE)} (Free) | {formatFileSize(MAX_FILE_SIZE_PREMIUM)} (Premium)
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* YouTube Upload */}
      {uploadMode === 'youtube' && (
        <div className="space-y-6">
          {isUploading ? (
            <div className="card text-center space-y-4">
              <Loader2 className="w-12 h-12 text-primary-400 mx-auto animate-spin" />
              <div>
                <p className="text-white font-medium mb-2">Processing YouTube video...</p>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-white/70 text-sm mt-1">{uploadProgress}%</p>
              </div>
            </div>
          ) : (
            <div className="card space-y-4">
              <div className="text-center mb-6">
                <Play className="w-16 h-16 text-white/50 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Import from YouTube</h3>
                <p className="text-white/70">Paste any YouTube video URL to get started</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-white/80 font-medium mb-2">
                    YouTube URL
                  </label>
                  <input
                    type="url"
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                    placeholder="https://www.youtube.com/watch?v=..."
                    className="input-field w-full"
                  />
                </div>

                <div>
                  <label className="block text-white/80 font-medium mb-2">
                    Video Title
                  </label>
                  <input
                    type="text"
                    value={videoTitle}
                    onChange={(e) => setVideoTitle(e.target.value)}
                    placeholder="Enter a title for your video"
                    className="input-field w-full"
                  />
                </div>

                <button
                  onClick={handleYouTubeUpload}
                  disabled={!youtubeUrl || !videoTitle}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <LinkIcon className="w-4 h-4 inline mr-2" />
                  Import from YouTube
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tips */}
      <div className="mt-8 text-center">
        <p className="text-white/60 text-sm">
          💡 <strong>Pro tip:</strong> Videos with clear speech and engaging content work best for viral clips
        </p>
      </div>
    </div>
  )
}
