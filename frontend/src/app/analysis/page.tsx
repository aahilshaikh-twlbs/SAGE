'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { ArrowLeft, Play, Pause, RotateCcw, Settings, Loader2 } from 'lucide-react';

interface VideoData {
  id: string;
  filename: string;
  embedding_id: string;
  video_id: string;
  duration: number;
}

interface Difference {
  start_sec: number;
  end_sec: number;
  distance: number;
}

interface ComparisonResult {
  filename1: string;
  filename2: string;
  differences: Difference[];
  total_segments: number;
  differing_segments: number;
  threshold_used: number;
}

export default function AnalysisPage() {
  const router = useRouter();
  const [video1, setVideo1] = useState<VideoData | null>(null);
  const [video2, setVideo2] = useState<VideoData | null>(null);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [threshold, setThreshold] = useState(0.1);
  const [distanceMetric, setDistanceMetric] = useState<'cosine' | 'euclidean'>('cosine');
  const [showSettings, setShowSettings] = useState(false);

  // Video player states
  const [isPlaying1, setIsPlaying1] = useState(false);
  const [isPlaying2, setIsPlaying2] = useState(false);

  useEffect(() => {
    // Load video data from session storage
    const video1Data = sessionStorage.getItem('video1_data');
    const video2Data = sessionStorage.getItem('video2_data');

    if (!video1Data || !video2Data) {
      setError('Video data not found. Please upload videos first.');
      return;
    }

    try {
      setVideo1(JSON.parse(video1Data));
      setVideo2(JSON.parse(video2Data));
    } catch (error) {
      setError('Invalid video data. Please upload videos again.');
    }
  }, []);

  const handleCompare = async () => {
    if (!video1 || !video2) return;

    setIsComparing(true);
    setError(null);

    try {
      const result = await api.compareVideos(
        video1.embedding_id,
        video2.embedding_id,
        threshold,
        distanceMetric
      );
      setComparisonResult(result);
    } catch (error) {
      console.error('Comparison failed:', error);
      setError('Failed to compare videos. Please try again.');
    } finally {
      setIsComparing(false);
    }
  };

  const togglePlay1 = () => {
    const video = document.getElementById('video1') as HTMLVideoElement;
    if (video) {
      if (isPlaying1) {
        video.pause();
        setIsPlaying1(false);
      } else {
        video.play();
        setIsPlaying1(true);
      }
    }
  };

  const togglePlay2 = () => {
    const video = document.getElementById('video2') as HTMLVideoElement;
    if (video) {
      if (isPlaying2) {
        video.pause();
        setIsPlaying2(false);
      } else {
        video.play();
        setIsPlaying2(true);
      }
    }
  };

  const seekToTime = (time: number) => {
    const video1 = document.getElementById('video1') as HTMLVideoElement;
    const video2 = document.getElementById('video2') as HTMLVideoElement;
    
    if (video1) video1.currentTime = time;
    if (video2) video2.currentTime = time;
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (error) {
    return (
      <div className="min-h-screen bg-sage-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={() => router.push('/')} className="bg-sage-500 hover:bg-sage-600">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Upload
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!video1 || !video2) {
    return (
      <div className="min-h-screen bg-sage-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-sage-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-sage-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-sage-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Button
              onClick={() => router.push('/')}
              variant="outline"
              size="sm"
              className="border-sage-200 hover:bg-sage-50 text-sage-400"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Upload
            </Button>
            
            <div className="flex items-center gap-4">
              <Button
                onClick={() => setShowSettings(!showSettings)}
                variant="outline"
                size="sm"
                className="border-sage-200 hover:bg-sage-50 text-sage-400"
              >
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
              
              <Button
                onClick={handleCompare}
                disabled={isComparing}
                className="bg-sage-500 hover:bg-sage-600 text-white"
              >
                {isComparing ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RotateCcw className="w-4 h-4 mr-2" />
                )}
                {isComparing ? 'Comparing...' : 'Compare Videos'}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Video 1 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sage-400">{video1.filename}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <video
                  id="video1"
                  className="w-full rounded-lg"
                  onPlay={() => setIsPlaying1(true)}
                  onPause={() => setIsPlaying1(false)}
                  controls
                >
                  <source src={`/api/serve-video/${video1.video_id}`} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
                
                <div className="flex items-center justify-between">
                  <div className="text-sm text-sage-300">
                    Duration: {formatTime(video1.duration)}
                  </div>
                  <Button
                    onClick={togglePlay1}
                    size="sm"
                    variant="outline"
                    className="border-sage-200 hover:bg-sage-50 text-sage-400"
                  >
                    {isPlaying1 ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Video 2 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sage-400">{video2.filename}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <video
                  id="video2"
                  className="w-full rounded-lg"
                  onPlay={() => setIsPlaying2(true)}
                  onPause={() => setIsPlaying2(false)}
                  controls
                >
                  <source src={`/api/serve-video/${video2.video_id}`} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
                
                <div className="flex items-center justify-between">
                  <div className="text-sm text-sage-300">
                    Duration: {formatTime(video2.duration)}
                  </div>
                  <Button
                    onClick={togglePlay2}
                    size="sm"
                    variant="outline"
                    className="border-sage-200 hover:bg-sage-50 text-sage-400"
                  >
                    {isPlaying2 ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Comparison Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-sage-400 mb-2">
                    Similarity Threshold
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={threshold}
                    onChange={(e) => setThreshold(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-sage-300 mt-1">
                    Current: {threshold.toFixed(2)} ({threshold < 0.3 ? 'Strict' : threshold < 0.7 ? 'Moderate' : 'Loose'})
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-sage-400 mb-2">
                    Distance Metric
                  </label>
                  <select
                    value={distanceMetric}
                    onChange={(e) => setDistanceMetric(e.target.value as 'cosine' | 'euclidean')}
                    className="w-full p-2 border border-sage-200 rounded-md bg-white text-sage-400"
                  >
                    <option value="cosine">Cosine Distance</option>
                    <option value="euclidean">Euclidean Distance</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Comparison Results */}
        {comparisonResult && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Comparison Results
                <Badge variant="secondary" className="bg-sage-100 text-sage-600">
                  {comparisonResult.differing_segments} differences found
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-sage-50 rounded-lg">
                    <div className="text-2xl font-bold text-sage-500">{comparisonResult.total_segments}</div>
                    <div className="text-sm text-sage-400">Total Segments</div>
                  </div>
                  <div className="text-center p-4 bg-sage-50 rounded-lg">
                    <div className="text-2xl font-bold text-sage-500">{comparisonResult.differing_segments}</div>
                    <div className="text-sm text-sage-400">Different Segments</div>
                  </div>
                  <div className="text-center p-4 bg-sage-50 rounded-lg">
                    <div className="text-2xl font-bold text-sage-500">{comparisonResult.threshold_used}</div>
                    <div className="text-sm text-sage-400">Threshold Used</div>
                  </div>
                </div>

                {/* Timeline */}
                <div>
                  <h4 className="font-medium text-sage-400 mb-3">Timeline of Differences</h4>
                  <div className="space-y-2">
                    {comparisonResult.differences.map((diff, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-4 p-3 bg-red-50 border border-red-200 rounded-lg cursor-pointer hover:bg-red-100 transition-colors"
                        onClick={() => seekToTime(diff.start_sec)}
                      >
                        <div className="flex-1">
                          <div className="font-medium text-red-700">
                            {formatTime(diff.start_sec)} - {formatTime(diff.end_sec)}
                          </div>
                          <div className="text-sm text-red-600">
                            Distance: {diff.distance.toFixed(4)}
                          </div>
                        </div>
                        <Badge variant="destructive" className="bg-red-100 text-red-700">
                          Different
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
