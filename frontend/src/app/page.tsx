'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ApiKeyConfig } from '@/components/ApiKeyConfig';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { Video, Loader2, X, Play, Upload, CheckCircle, AlertCircle, StopCircle } from 'lucide-react';

interface LocalVideo {
  id: string;
  file: File;
  thumbnail: string;
  video_id?: string;
  embedding_id?: string;
  status: 'uploading' | 'processing' | 'ready' | 'error' | 'cancelled' | 'uploaded';
  error?: string;
  duration?: number;
  progress?: string;
}

export default function LandingPage() {
  const router = useRouter();
  const [showApiKeyConfig, setShowApiKeyConfig] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadedVideos, setUploadedVideos] = useState<LocalVideo[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Check for stored API key on component mount
  useEffect(() => {
    const checkStoredApiKey = async () => {
      try {
        const storedKey = localStorage.getItem('sage_api_key');
        if (storedKey) {
          const result = await api.validateApiKey(storedKey);
          if (result.isValid) {
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
        // If it's a connection error, show the API key config to let user retry
        if (error instanceof Error && error.message.includes('Failed to fetch')) {
          setError('Cannot connect to backend. Please check your connection and try again.');
          setShowApiKeyConfig(true);
        } else {
          // For other errors, just show the API key config
          setShowApiKeyConfig(true);
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkStoredApiKey();
  }, []);

  // Poll for video status updates
  useEffect(() => {
    const pollStatus = async () => {
      // Get current videos using functional update to avoid stale closure
      setUploadedVideos(currentVideos => {
        // Don't poll if no videos or no videos need polling
        const needsPolling = currentVideos.some(v => 
          v.video_id && (v.status === 'processing' || v.status === 'uploading' || v.status === 'uploaded')
        );
        
        if (currentVideos.length === 0 || !needsPolling) return currentVideos;
        
        const updatedVideos = [...currentVideos];
        let hasChanges = false;

                 // Process each video that needs polling
         for (let i = 0; i < updatedVideos.length; i++) {
           const video = updatedVideos[i];
           if (video.video_id && (video.status === 'processing' || video.status === 'uploading' || video.status === 'uploaded')) {
             try {
               // Use a separate async function to handle the API call
               (async () => {
                 try {
                   const status = await api.getVideoStatus(video.video_id!);
                  
                  // Determine the current stage based on status
                  let newStatus: LocalVideo['status'] = video.status;
                  let progress = video.progress;
                  
                  if (status.status === 'ready') {
                    newStatus = 'ready';
                    progress = 'Completed';
                  } else if (status.embedding_status === 'processing') {
                    newStatus = 'processing';
                    progress = 'Generating embeddings...';
                  } else if (status.embedding_status === 'pending') {
                    newStatus = 'processing';
                    progress = 'Preparing embedding task...';
                  } else if (status.embedding_status === 'failed') {
                    newStatus = 'error';
                    progress = 'Embedding generation failed';
                  } else if (status.embedding_status === 'cancelled') {
                    newStatus = 'cancelled';
                    progress = 'Cancelled';
                  } else if (status.status === 'uploaded' && status.embedding_status === 'pending') {
                    newStatus = 'processing';
                    progress = 'Starting embedding generation...';
                  }
                  
                  // Update the video if there are changes
                  if (newStatus !== video.status || progress !== video.progress || status.duration !== video.duration) {
                    setUploadedVideos(prevVideos => 
                      prevVideos.map(v => 
                        v.id === video.id 
                          ? { ...v, status: newStatus, progress, duration: status.duration }
                          : v
                      )
                    );
                  }
                } catch (error) {
                  console.error('Error checking video status:', error);
                }
              })();
            } catch (error) {
              console.error('Error in polling loop:', error);
            }
          }
        }

        return updatedVideos;
      });
    };

    const interval = setInterval(pollStatus, 3000); // Poll every 3 seconds for more responsive updates
    return () => clearInterval(interval);
  }, []); // Empty dependency array to prevent re-creation of polling

  const handleKeyValidated = (key: string) => {
    localStorage.setItem('sage_api_key', key);
    setShowApiKeyConfig(false);
    setError(null); // Clear any connection errors
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
    
    // Check if we already have 2 videos
    if (uploadedVideos.length >= 2) {
      alert('Maximum 2 videos allowed');
      return;
    }
    
    // Allow selecting the same video twice for comparison
    // No duplicate check needed - user can compare a video with itself
    
    const thumbnail = await generateThumbnail(file);
    const newVideo: LocalVideo = {
      id: `video-${Date.now()}`,
      file,
      thumbnail,
      status: 'uploading',
      progress: 'Uploading to S3...'
    };
    
    setUploadedVideos(prev => [...prev, newVideo]);
    
    try {
      const result = await api.uploadVideo(file);
      
      setUploadedVideos(prev => prev.map(video => 
        video.id === newVideo.id 
          ? { 
              ...video, 
              status: 'processing', 
              video_id: result.video_id, 
              embedding_id: result.embedding_id,
              progress: 'Starting embedding generation...'
            }
          : video
      ));
      
    } catch (error) {
      console.error('Upload failed:', error);
      let errorMessage = 'Upload failed';
      
      if (error instanceof Error) {
        if (error.message.includes('Failed to fetch')) {
          errorMessage = 'Cannot connect to backend. Please check your connection.';
        } else if (error.message.includes('Upload failed')) {
          errorMessage = error.message;
        }
      }
      
      setUploadedVideos(prev => prev.map(video => 
        video.id === newVideo.id 
          ? { ...video, status: 'error', error: errorMessage }
          : video
      ));
      
      // Also show error at the top level
      setError(errorMessage);
    }
    
    // Reset file input
    event.target.value = '';
  };

  const cancelVideo = async (video: LocalVideo) => {
    if (video.video_id && (video.status === 'processing' || video.status === 'uploading')) {
      try {
        // Cancel the entire video processing (includes embedding task)
        await api.cancelVideo(video.video_id);
        setUploadedVideos(prev => prev.map(v => 
          v.id === video.id 
            ? { ...v, status: 'cancelled', progress: 'Cancelled' }
            : v
        ));
      } catch (error) {
        console.error('Error cancelling video:', error);
        setError('Failed to cancel video. Please try again.');
      }
    } else {
      // Just remove from list if not processing
      setUploadedVideos(prev => prev.filter(v => v.id !== video.id));
    }
    // Clear any error messages when removing videos
    setError(null);
  };

  const removeVideo = async (videoId: string) => {
    const video = uploadedVideos.find(v => v.id === videoId);
    if (video && video.video_id && (video.status === 'processing' || video.status === 'uploading')) {
      try {
        // Cancel the entire video processing
        await api.cancelVideo(video.video_id);
      } catch (error) {
        console.error('Error cancelling video during removal:', error);
        // Continue with removal even if cancellation fails
      }
    }
    
    setUploadedVideos(prev => prev.filter(video => video.id !== videoId));
    // Clear any error messages when removing videos
    setError(null);
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
        duration: video.duration || 60
      }));
    });
    
    router.push('/analysis');
  };

  const getStatusDisplay = (video: LocalVideo) => {
    switch (video.status) {
      case 'uploading':
        return (
          <div className="flex items-center gap-2 text-sage-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{video.progress || 'Uploading...'}</span>
          </div>
        );
      case 'processing':
        return (
          <div className="flex items-center gap-2 text-sage-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{video.progress || 'Processing...'}</span>
          </div>
        );
      case 'ready':
        return (
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle className="w-4 h-4" />
            <span>Ready</span>
          </div>
        );
      case 'error':
        return (
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span>{video.error || 'Error'}</span>
          </div>
        );
      case 'cancelled':
        return (
          <div className="flex items-center gap-2 text-gray-500">
            <StopCircle className="w-4 h-4" />
            <span>Cancelled</span>
          </div>
        );
      case 'uploaded':
        return (
          <div className="flex items-center gap-2 text-sage-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Starting embedding generation...</span>
          </div>
        );
      default:
        return null;
    }
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
              {/* Connection Status */}
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${error && error.includes('Cannot connect') ? 'bg-red-500' : 'bg-green-500'}`}></div>
                <span className="text-sm text-sage-300">
                  {error && error.includes('Cannot connect') ? 'Backend Offline' : 'Backend Online'}
                </span>
              </div>
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
                      {/* eslint-disable-next-line @next/next/no-img-element */}
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
                        {video.duration && (
                          <p className="text-sm text-sage-300">
                            Duration: {Math.floor(video.duration / 60)}:{(video.duration % 60).toFixed(0).padStart(2, '0')}
                          </p>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {getStatusDisplay(video)}
                        
                        <Button
                          onClick={() => cancelVideo(video)}
                          variant="outline"
                          size="sm"
                          className="border-sage-200 hover:bg-sage-50 text-sage-400"
                        >
                          {video.status === 'processing' || video.status === 'uploading' ? (
                            <StopCircle className="w-4 h-4" />
                          ) : (
                            <X className="w-4 h-4" />
                          )}
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
