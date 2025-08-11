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

    // Client upload via @vercel/blob/client.helper endpoint
    const uploadRes = await fetch(`${API_BASE_URL}/blob/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pathname: `videos/${file.name}`,
        contentType: file.type || 'video/mp4',
        access: 'public',
        multipart: true,
        clientPayload: 'sage-video',
      }),
    });
    if (!uploadRes.ok) throw new ApiError('Failed to initiate client upload', uploadRes.status);
    const tokenPayload = await uploadRes.json();
    // tokenPayload contains client token info that upload() uses under the hood; however
    // since handleUpload returns a token for client uploader, we will directly upload with fetch

    // As a simple approach: use the URL returned when handleUpload completes (blob.upload-completed callback)
    // But since it is async callback, we do a direct put fallback when needed
    // For simplicity, retry with direct PUT
    const putRes = await fetch(tokenPayload.url ?? tokenPayload.uploadUrl ?? '', { method: 'POST', body: file });
    const blob = putRes.ok ? await putRes.json() : tokenPayload.blob ?? tokenPayload;

    const headers: Record<string, string> = {};
    const keyToUse = apiKey || localStorage.getItem('sage_api_key');
    if (keyToUse) headers['X-API-Key'] = keyToUse;

    // Tell backend to ingest the blob URL
    const ingest = await fetch(`${API_BASE_URL}/ingest-blob`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify({ blob_url: blob.url, filename: file.name }),
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