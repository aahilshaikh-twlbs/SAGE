import { ApiKeyConfig } from '@/types';
import { upload } from '@vercel/blob/client';

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

  // Upload to Vercel Blob on the client, then send blob URL to backend for embedding
  uploadAndGenerateEmbeddings: async (formData: FormData, apiKey?: string): Promise<{
    embeddings: unknown;
    filename: string;
    duration: number;
    embedding_id: string;
    video_url: string;
  }> => {
    const file = formData.get('file') as File;
    if (!file) throw new Error('file missing');

    // Client-side multipart upload directly to Vercel Blob (avoids 413 on Vercel functions)
    const { url } = await upload(`videos/${file.name}`, file, {
      access: 'public',
      multipart: true,
      handleUploadUrl: '/api/blob/upload',
    });

    const headers: Record<string, string> = {};
    const keyToUse = apiKey || localStorage.getItem('sage_api_key');
    if (keyToUse) headers['X-API-Key'] = keyToUse;

    // Tell backend to ingest the blob URL
    const ingest = await fetch(`${API_BASE_URL}/ingest-blob`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify({ blob_url: url, filename: file.name }),
    });
    if (!ingest.ok) throw new ApiError('Ingest failed', ingest.status);
    return ingest.json();
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