'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ApiKeyConfig } from '@/components/ApiKeyConfig';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { Video, Loader2, X, Play, Upload } from 'lucide-react';

interface LocalVideo {
  id: string;
  file: File;
  thumbnail: string;
  video_id?: string;
  embedding_id?: string;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  error?: string;
}

export default function LandingPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState('');
  const [showApiKeyConfig, setShowApiKeyConfig] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadedVideos, setUploadedVideos] = useState<LocalVideo[]>([]);
  const [isGeneratingEmbeddings, setIsGeneratingEmbeddings] = useState(false);
  const [embeddingProgress, setEmbeddingProgress] = useState<{[key: string]: string}>({});
  const [error, setError] = useState<string | null>(null);

  // Check for stored API key on component mount
  useEffect(() => {
    const checkStoredApiKey = async () => {
      try {
        const storedKey = localStorage.getItem('sage_api_key');
        if (storedKey) {
          const result = await api.validateApiKey(storedKey);
          if (result.isValid) {
            setApiKey(storedKey);
            setShowApiKeyConfig(false);
          } else {
            localStorage.removeItem('sage_api_key');
            setShowApiKeyConfig(true);
          }
        } else {
          setShowApiKeyConfig(true);
        }
      } catch (error) {
        console.error('Error checking stored API key:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkStoredApiKey();
  }, []);

  const handleKeyValidated = (key: string) => {
    setApiKey(key);
    localStorage.setItem('sage_api_key', key);
    setShowApiKeyConfig(false);
  };

  const generateThumbnail = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const video = document.createElement('video');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;
      
      video.onloadedmetadata = () => {
        video.currentTime = 1; // Seek to 1 second
      };
      
      video.onseeked = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL());
      };
      
      video.src = URL.createObjectURL(file);
    });
  };

  const handleVideoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const file = files[0];
    if (uploadedVideos.length >= 2) {
      alert('Maximum 2 videos allowed');
      return;
    }
    
    const thumbnail = await generateThumbnail(file);
    const newVideo: LocalVideo = {
      id: `video-${Date.now()}`,
      file,
      thumbnail,
      status: 'uploading'
    };
    
    setUploadedVideos(prev => [...prev, newVideo]);
    
    try {
      const result = await api.uploadVideo(file);
      
      setUploadedVideos(prev => prev.map(video => 
        video.id === newVideo.id 
          ? { ...video, status: 'processing', video_id: result.video_id, embedding_id: result.embedding_id }
          : video
      ));
      
      // Simulate processing time
      setTimeout(() => {
        setUploadedVideos(prev => prev.map(video => 
          video.id === newVideo.id 
            ? { ...video, status: 'ready' }
            : video
        ));
      }, 2000);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadedVideos(prev => prev.map(video => 
        video.id === newVideo.id 
          ? { ...video, status: 'error', error: 'Upload failed' }
          : video
      ));
    }
    
    // Reset file input
    event.target.value = '';
  };

  const removeVideo = (videoId: string) => {
    setUploadedVideos(prev => prev.filter(video => video.id !== videoId));
  };

  const startComparison = () => {
    const readyVideos = uploadedVideos.filter(video => video.status === 'ready');
    if (readyVideos.length !== 2) {
      setError('Please upload and process 2 videos before starting comparison');
      return;
    }
    
    // Store video data in session storage for analysis page
    readyVideos.forEach((video, index) => {
      sessionStorage.setItem(`video${index + 1}_data`, JSON.stringify({
        id: video.id,
        filename: video.file.name,
        embedding_id: video.embedding_id,
        video_id: video.video_id,
        duration: 60 // Mock duration
      }));
    });
    
    router.push('/analysis');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-sage-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-sage-500" />
          <p className="text-sage-400">Loading SAGE...</p>
        </div>
      </div>
    );
  }

  if (showApiKeyConfig) {
    return (
      <div className="min-h-screen bg-sage-50 flex items-center justify-center p-4">
        <ApiKeyConfig onKeyValidated={handleKeyValidated} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-sage-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-sage-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="w-8 h-8 bg-sage-500 rounded-lg flex items-center justify-center">
                <Video className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-semibold text-sage-400">SAGE</h1>
            </div>
            
            <Button
              onClick={() => setShowApiKeyConfig(true)}
              variant="outline"
              size="sm"
              className="border-sage-200 hover:bg-sage-50 text-sage-400"
            >
              Change API Key
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-sage-400 mb-4">
            AI-Powered Video Comparison
          </h2>
          <p className="text-lg text-sage-300 max-w-2xl mx-auto">
            Upload two videos and let our AI analyze them for differences using TwelveLabs embeddings.
          </p>
        </div>

        {/* Upload Section */}
        <div className="max-w-4xl mx-auto">
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload Videos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleVideoUpload}
                  className="hidden"
                  id="video-upload"
                  disabled={uploadedVideos.length >= 2}
                />
                <label
                  htmlFor="video-upload"
                  className={`inline-flex items-center gap-2 px-6 py-3 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                    uploadedVideos.length >= 2
                      ? 'border-sage-200 text-sage-300 cursor-not-allowed'
                      : 'border-sage-300 text-sage-400 hover:border-sage-500 hover:text-sage-500'
                  }`}
                >
                  <Video className="w-5 h-5" />
                  {uploadedVideos.length >= 2 ? 'Maximum videos reached' : 'Choose video file'}
                </label>
                <p className="text-sm text-sage-300 mt-2">
                  MP4 format recommended. Maximum 2 videos.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Video List */}
          {uploadedVideos.length > 0 && (
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Uploaded Videos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {uploadedVideos.map((video) => (
                    <div
                      key={video.id}
                      className="flex items-center gap-4 p-4 border border-sage-200 rounded-lg"
                    >
                      <img
                        src={video.thumbnail}
                        alt="Video thumbnail"
                        className="w-20 h-12 object-cover rounded"
                      />
                      <div className="flex-1">
                        <h4 className="font-medium text-sage-400">{video.file.name}</h4>
                        <p className="text-sm text-sage-300">
                          {video.file.size > 1024 * 1024
                            ? `${(video.file.size / (1024 * 1024)).toFixed(1)} MB`
                            : `${(video.file.size / 1024).toFixed(1)} KB`
                          }
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {video.status === 'uploading' && (
                          <div className="flex items-center gap-2 text-sage-500">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Uploading...
                          </div>
                        )}
                        {video.status === 'processing' && (
                          <div className="flex items-center gap-2 text-sage-500">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Processing...
                          </div>
                        )}
                        {video.status === 'ready' && (
                          <div className="flex items-center gap-2 text-green-600">
                            <Play className="w-4 h-4" />
                            Ready
                          </div>
                        )}
                        {video.status === 'error' && (
                          <div className="flex items-center gap-2 text-red-600">
                            <X className="w-4 h-4" />
                            {video.error}
                          </div>
                        )}
                        
                        <Button
                          onClick={() => removeVideo(video.id)}
                          variant="outline"
                          size="sm"
                          className="border-sage-200 hover:bg-sage-50 text-sage-400"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error Display */}
          {error && (
            <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">{error}</p>
              <Button
                onClick={() => setError(null)}
                variant="outline"
                size="sm"
                className="mt-2 border-red-200 hover:bg-red-50 text-red-600"
              >
                Dismiss
              </Button>
            </div>
          )}

          {/* Start Comparison Button */}
          {uploadedVideos.filter(v => v.status === 'ready').length === 2 && (
            <div className="text-center">
              <Button
                onClick={startComparison}
                size="lg"
                className="bg-sage-500 hover:bg-sage-600 text-white px-8 py-3"
              >
                <Play className="w-5 h-5 mr-2" />
                Start Comparison
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
