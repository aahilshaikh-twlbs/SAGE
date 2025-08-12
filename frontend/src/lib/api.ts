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
  uploadAndGenerateEmbeddings: async (formData: FormData, apiKey?: string, onProgress?: (status: string, progress?: string) => void): Promise<{
    embeddings: unknown;
    filename: string;
    duration: number;
    embedding_id: string;
    video_url: string;
  }> => {
    const file = formData.get('file') as File;
    if (!file) throw new Error('file missing');

    console.log(`[Blob Upload] Starting upload for ${file.name} (${(file.size / (1024*1024)).toFixed(2)} MB)`);
    
    let url: string;
    try {
      // Client-side multipart upload directly to Vercel Blob (avoids 413 on Vercel functions)
      const result = await upload(`videos/${file.name}`, file, {
        access: 'public',
        multipart: file.size > 300 * 1024 * 1024, // Use multipart for files > 300MB
        handleUploadUrl: '/api/blob/upload',
        onUploadProgress: ({ percentage }) => {
          console.log(`[Blob Upload] Progress: ${percentage}%`);
          if (onProgress) {
            onProgress('uploading', `${percentage}%`);
          }
        },
      });
      url = result.url;
      console.log(`[Blob Upload] Completed. URL: ${url}`);
    } catch (uploadError) {
      console.error('[Blob Upload] Failed:', uploadError);
      // Provide more detailed error info
      const errorMessage = uploadError instanceof Error 
        ? uploadError.message 
        : typeof uploadError === 'object' && uploadError !== null
          ? JSON.stringify(uploadError)
          : String(uploadError);
      throw new ApiError(`Blob upload failed: ${errorMessage}`, 500);
    }

    const headers: Record<string, string> = {};
    const keyToUse = apiKey || localStorage.getItem('sage_api_key');
    if (keyToUse) headers['X-API-Key'] = keyToUse;

    // Tell backend to ingest the blob URL
    // Call via Vercel rewrite to avoid mixed content (HTTPS)
    const ingest = await fetch(`${API_BASE_URL}/ingest-blob`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify({ blob_url: url, filename: file.name }),
    });
    if (!ingest.ok) {
      const errorData = await ingest.json().catch(() => ({ detail: ingest.statusText }));
      throw new ApiError(`Ingest failed: ${errorData.detail || ingest.statusText}`, ingest.status);
    }
    
    const { task_id } = await ingest.json();
    
    // Poll for status
    const maxWaitTime = 30 * 60 * 1000; // 30 minutes max
    const pollInterval = 5000; // 5 seconds
    const startTime = Date.now();
    
    console.log(`[Polling] Starting to poll task ${task_id}`);
    
    while (Date.now() - startTime < maxWaitTime) {
      try {
        const statusRes = await fetch(`${API_BASE_URL}/ingest-blob/status/${task_id}`, {
          headers,
          // Add timeout to prevent hanging requests
          signal: AbortSignal.timeout(10000), // 10 second timeout per request
        });
        
        if (!statusRes.ok) {
          console.error(`[Polling] Status request failed: ${statusRes.status}`);
          throw new ApiError('Failed to get task status', statusRes.status);
        }
      
      const status = await statusRes.json();
      console.log(`Task ${task_id} status:`, status.status, status.progress || '');
      
      // Add time estimates to progress message
      let progressMessage = status.progress || '';
      if (status.estimated_remaining_seconds) {
        const minutes = Math.floor(status.estimated_remaining_seconds / 60);
        const seconds = status.estimated_remaining_seconds % 60;
        progressMessage += ` (est. ${minutes}m ${seconds}s remaining)`;
      }
      
      // Call progress callback if provided
      if (onProgress) {
        onProgress(status.status, progressMessage);
      }
      
      if (status.status === 'completed') {
        return status;
      } else if (status.status === 'failed') {
        throw new ApiError(`Task failed: ${status.error}`, 500);
      }
      
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      } catch (error) {
        console.error('[Polling] Error during status check:', error);
        
        // If it's a network error or timeout, continue polling
        if (error instanceof TypeError || (error instanceof Error && error.name === 'AbortError')) {
          console.log('[Polling] Network error, continuing to poll...');
          await new Promise(resolve => setTimeout(resolve, pollInterval));
          continue;
        }
        
        // For other errors, re-throw
        throw error;
      }
    }
    
    throw new ApiError('Task timed out after 30 minutes', 408);
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