import { ApiKeyConfig } from '@/types';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  apiKey?: string
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  
  // Use provided key or get from localStorage
  const keyToUse = apiKey || localStorage.getItem('sage_api_key');
  if (keyToUse) {
    headers['X-API-Key'] = keyToUse;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers,
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(
      errorData?.detail || `Request failed: ${response.statusText}`,
      response.status
    );
  }

  return response.json();
}

export const api = {
  // API Key validation
  validateApiKey: async (key: string): Promise<ApiKeyConfig> => {
    return apiRequest<ApiKeyConfig>('/validate-key', {
      method: 'POST',
      body: JSON.stringify({ key }),
    }, key);
  },

  // Upload video to S3 and start embedding generation
  uploadAndGenerateEmbeddings: async (formData: FormData, apiKey?: string): Promise<{
    message: string;
    filename: string;
    video_id: string;
    embedding_id: string;
    status: string;
  }> => {
    const headers: Record<string, string> = {};
    const keyToUse = apiKey || localStorage.getItem('sage_api_key');
    if (keyToUse) {
      headers['X-API-Key'] = keyToUse;
    }
    // Don't set Content-Type for FormData - let browser set it with boundary

    const response = await fetch(`${API_BASE_URL}/upload-and-generate-embeddings`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(`Upload failed: ${errorData.detail || response.statusText}`, response.status);
    }

    return response.json();
  },

  // Check video status
  getVideoStatus: async (videoId: string, apiKey?: string): Promise<{
    video_id: string;
    filename: string;
    status: string;
    embedding_status: string;
    duration?: number;
    upload_timestamp: string;
  }> => {
    return apiRequest(`/video-status/${videoId}`, {
      method: 'GET',
    }, apiKey);
  },

  // Check embedding status
  getEmbeddingStatus: async (embeddingId: string, apiKey?: string): Promise<{
    embedding_id: string;
    filename: string;
    status: string;
    duration?: number;
    completed_at?: string;
    error?: string;
  }> => {
    return apiRequest(`/embedding-status/${embeddingId}`, {
      method: 'GET',
    }, apiKey);
  },

  // Get video URL (presigned S3 URL)
  getVideoUrl: async (videoId: string, apiKey?: string): Promise<{
    video_url: string;
  }> => {
    return apiRequest(`/serve-video/${videoId}`, {
      method: 'GET',
    }, apiKey);
  },

  // Compare local videos
  compareLocalVideos: async (embeddingId1: string, embeddingId2: string, threshold: number = 0.1, apiKey?: string): Promise<{
    filename1: string;
    filename2: string;
    differences: Array<{
      start_sec: number;
      end_sec: number;
      distance: number;
    }>;
    total_segments: number;
    differing_segments: number;
    threshold_used: number;
  }> => {
    const params = new URLSearchParams({
      embedding_id1: embeddingId1,
      embedding_id2: embeddingId2,
      threshold: threshold.toString()
    });
    
    return apiRequest(`/compare-local-videos?${params}`, {
      method: 'POST',
    }, apiKey);
  },
};