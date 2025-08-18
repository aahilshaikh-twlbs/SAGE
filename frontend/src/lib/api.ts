const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiKeyResponse {
  key: string;
  isValid: boolean;
}

export interface VideoUploadResponse {
  message: string;
  filename: string;
  video_id: string;
  embedding_id: string;
  status: string;
}

export interface Difference {
  start_sec: number;
  end_sec: number;
  distance: number;
}

export interface ComparisonResponse {
  filename1: string;
  filename2: string;
  differences: Difference[];
  total_segments: number;
  differing_segments: number;
  threshold_used: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  uptime: string;
  timestamp: string;
  database_status: string;
  python_version: string;
}

export interface VideoStatusResponse {
  video_id: string;
  filename: string;
  status: string;
  embedding_status: string;
  duration?: number;
  upload_timestamp: string;
}

export interface EmbeddingStatusResponse {
  embedding_id: string;
  filename: string;
  status: string;
  duration?: number;
  completed_at?: string;
  error?: string;
}

export interface CancelTaskResponse {
  message: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async validateApiKey(key: string): Promise<ApiKeyResponse> {
    return this.request<ApiKeyResponse>('/validate-key', {
      method: 'POST',
      body: JSON.stringify({ key }),
    });
  }

  async uploadVideo(file: File): Promise<VideoUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload-and-generate-embeddings`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async cancelEmbeddingTask(embeddingId: string): Promise<CancelTaskResponse> {
    return this.request<CancelTaskResponse>(`/cancel-embedding-task/${embeddingId}`, {
      method: 'POST',
    });
  }

  async cancelVideo(videoId: string): Promise<CancelTaskResponse> {
    return this.request<CancelTaskResponse>(`/cancel-video/${videoId}`, {
      method: 'POST',
    });
  }

  async compareVideos(
    embeddingId1: string,
    embeddingId2: string,
    threshold: number = 0.1,
    distanceMetric: 'cosine' | 'euclidean' = 'cosine'
  ): Promise<{
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
  }> {
    const params = new URLSearchParams({
      embedding_id1: embeddingId1,
      embedding_id2: embeddingId2,
      threshold: threshold.toString(),
      distance_metric: distanceMetric
    });
    
    return this.request<{
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
    }>(`/compare-local-videos?${params}`, {
      method: 'POST',
    });
  }

  async getVideoStatus(videoId: string): Promise<VideoStatusResponse> {
    return this.request<VideoStatusResponse>(`/video-status/${videoId}`);
  }

  async getEmbeddingStatus(embeddingId: string): Promise<EmbeddingStatusResponse> {
    return this.request<EmbeddingStatusResponse>(`/embedding-status/${embeddingId}`);
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  getVideoUrl(videoId: string): Promise<string> {
    return this.request<{video_url: string}>(`/serve-video/${videoId}`)
      .then(response => response.video_url);
  }
}

export const api = new ApiClient(API_BASE_URL);
export { API_BASE_URL };
