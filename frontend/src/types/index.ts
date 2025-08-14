export interface ApiKeyConfig {
  key: string;
  isValid: boolean;
}

export interface VideoData {
  id: string;
  filename: string;
  embedding_id: string;
  video_id: string;
  duration?: number;
  status: string;
  embedding_status: string;
  upload_timestamp: string;
}

export interface EmbeddingStatus {
  embedding_id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  duration?: number;
  completed_at?: string;
  error?: string;
}

export interface VideoStatus {
  video_id: string;
  filename: string;
  status: 'uploaded' | 'ready';
  embedding_status: string;
  duration?: number;
  upload_timestamp: string;
} 