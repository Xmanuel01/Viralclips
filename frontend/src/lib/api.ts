import axios from 'axios'
import { supabase } from './supabase'
import {
  VideoUploadRequest,
  VideoUploadResponse,
  TranscribeRequest,
  HighlightRequest,
  ExportRequest,
  JobStatusResponse,
  VideosResponse,
  HighlightsResponse,
  ClipsResponse,
  DownloadResponse,
  UserStats,
  ApiResponse
} from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance with auth header
const createApiClient = async () => {
  const { data: { session } } = await supabase.auth.getSession()
  
  return axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
      ...(session?.access_token && {
        'Authorization': `Bearer ${session.access_token}`
      })
    }
  })
}

export class ApiClient {
  static async uploadVideo(request: VideoUploadRequest): Promise<VideoUploadResponse> {
    const api = await createApiClient()
    const response = await api.post<VideoUploadResponse>('/upload', request)
    return response.data
  }

  static async uploadFile(videoId: string, file: File): Promise<ApiResponse> {
    const api = await createApiClient()
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post<ApiResponse>(`/upload-file?video_id=${videoId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }

  static async transcribeVideo(request: TranscribeRequest): Promise<ApiResponse> {
    const api = await createApiClient()
    const response = await api.post<ApiResponse>('/transcribe', request)
    return response.data
  }

  static async detectHighlights(request: HighlightRequest): Promise<ApiResponse> {
    const api = await createApiClient()
    const response = await api.post<ApiResponse>('/highlight', request)
    return response.data
  }

  static async exportClip(request: ExportRequest): Promise<ApiResponse> {
    const api = await createApiClient()
    const response = await api.post<ApiResponse>('/export', request)
    return response.data
  }

  static async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const api = await createApiClient()
    const response = await api.get<JobStatusResponse>(`/jobs/${jobId}/status`)
    return response.data
  }

  static async getUserVideos(): Promise<VideosResponse> {
    const api = await createApiClient()
    const response = await api.get<VideosResponse>('/videos')
    return response.data
  }

  static async getVideoHighlights(videoId: string): Promise<HighlightsResponse> {
    const api = await createApiClient()
    const response = await api.get<HighlightsResponse>(`/videos/${videoId}/highlights`)
    return response.data
  }

  static async getUserClips(): Promise<ClipsResponse> {
    const api = await createApiClient()
    const response = await api.get<ClipsResponse>('/clips')
    return response.data
  }

  static async getClipDownloadUrl(clipId: string): Promise<DownloadResponse> {
    const api = await createApiClient()
    const response = await api.get<DownloadResponse>(`/clips/${clipId}/download`)
    return response.data
  }

  static async getUserStats(): Promise<UserStats> {
    const api = await createApiClient()
    const response = await api.get<UserStats>('/user/stats')
    return response.data
  }

  // Paystack Payment Methods
  static async getPaymentPlans(): Promise<any> {
    const api = await createApiClient()
    const response = await api.get('/payment/plans')
    return response.data
  }

  static async initializePayment(planType: string): Promise<any> {
    const api = await createApiClient()
    const response = await api.post('/payment/initialize', { plan_type: planType })
    return response.data
  }

  static async verifyPayment(reference: string): Promise<any> {
    const api = await createApiClient()
    const response = await api.post('/payment/verify', { reference })
    return response.data
  }
}

// Utility functions for polling job status
export const pollJobStatus = async (
  jobId: string,
  onProgress: (status: JobStatusResponse) => void,
  interval: number = 2000
): Promise<JobStatusResponse> => {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await ApiClient.getJobStatus(jobId)
        onProgress(status)
        
        if (status.status === 'completed' || status.status === 'failed') {
          resolve(status)
        } else {
          setTimeout(poll, interval)
        }
      } catch (error) {
        reject(error)
      }
    }
    
    poll()
  })
}

// Format file size helper
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Format duration helper
export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }
}
