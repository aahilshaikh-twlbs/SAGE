'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api, API_BASE_URL } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Play, Pause, Settings } from 'lucide-react';

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

export default function AnalysisPage() {
  const router = useRouter();
  const [video1Data, setVideo1Data] = useState<VideoData | null>(null);
  const [video2Data, setVideo2Data] = useState<VideoData | null>(null);
  const [differences, setDifferences] = useState<Difference[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [threshold, setThreshold] = useState(0.05);
  const [showThresholdSettings, setShowThresholdSettings] = useState(false);
  const [totalSegments, setTotalSegments] = useState(0);
  const video1Ref = useRef<HTMLVideoElement>(null);
  const video2Ref = useRef<HTMLVideoElement>(null);

  const loadComparison = async (video1: VideoData, video2: VideoData, thresholdValue: number) => {
    try {
      setIsLoading(true);
      setError(null);
      const comparison = await api.compareLocalVideos(
        video1.embedding_id,
        video2.embedding_id,
        thresholdValue
      );
      
      setDifferences(comparison.differences);
      setTotalSegments(comparison.total_segments);
    } catch (err) {
      console.error('Error loading comparison:', err);
      setError('Failed to load comparison data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        // Get video data from session storage
        const video1Str = sessionStorage.getItem('video1_data');
        const video2Str = sessionStorage.getItem('video2_data');
        
        if (!video1Str || !video2Str) {
          setError('No video data found. Please upload videos first.');
          return;
        }
        
        const video1 = JSON.parse(video1Str) as VideoData;
        const video2 = JSON.parse(video2Str) as VideoData;
        
        setVideo1Data(video1);
        setVideo2Data(video2);
        
        // Compare videos with default threshold
        await loadComparison(video1, video2, threshold);
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load comparison data');
      }
    };
    
    loadData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleThresholdChange = async () => {
    if (video1Data && video2Data) {
      await loadComparison(video1Data, video2Data, threshold);
      setShowThresholdSettings(false);
    }
  };

  const handlePlayPause = () => {
    if (video1Ref.current && video2Ref.current) {
      if (isPlaying) {
        video1Ref.current.pause();
        video2Ref.current.pause();
      } else {
        video1Ref.current.play();
        video2Ref.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const seekToTime = (time: number) => {
    if (video1Ref.current && video2Ref.current) {
      video1Ref.current.currentTime = time;
      video2Ref.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleTimeUpdate = () => {
    if (video1Ref.current) {
      setCurrentTime(video1Ref.current.currentTime);
    }
  };

  const getSeverityColor = (distance: number, isFullVideo: boolean = false) => {
    // Special color for full video comparison
    if (isFullVideo) return 'bg-[#9B9896]'; // Medium grey for overall comparison
    
    if (distance === Infinity) return 'bg-[#DC2626]'; // Dark Red for missing segments
    if (distance > 0.4) return 'bg-[#EF4444]'; // Red for major differences
    if (distance > 0.3) return 'bg-[#F97316]'; // Orange for significant differences
    if (distance > 0.2) return 'bg-[#F59E0B]'; // Amber for moderate differences
    if (distance > 0.1) return 'bg-[#EAB308]'; // Yellow for minor differences
    if (distance > 0.05) return 'bg-[#84CC16]'; // Lime for very minor differences
    return 'bg-[#06B6D4]'; // Cyan for minimal differences
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (error || !video1Data || !video2Data) {
    return (
      <div className="min-h-screen bg-[#F4F3F3] flex items-center justify-center">
        <div className="text-center">
          <p className="text-[#EF4444] mb-4">{error || 'Failed to load video data'}</p>
          <Button 
            onClick={() => router.push('/')}
            className="bg-[#0066FF] hover:bg-[#0052CC] text-white"
          >
            Back to Upload
          </Button>
        </div>
      </div>
    );
  }

  const similarityPercent = totalSegments > 0 
    ? ((1 - differences.length / totalSegments) * 100).toFixed(1)
    : '0';

  return (
    <div className="min-h-screen bg-[#F4F3F3] text-[#1D1C1B]">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-[#D3D1CF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => router.push('/')}
                variant="outline"
                size="sm"
                className="flex items-center gap-2 border-[#D3D1CF] hover:bg-[#F4F3F3]"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Upload
              </Button>
              <h1 className="text-xl font-semibold">Video Comparison Analysis</h1>
            </div>
            
            <Button
              onClick={() => setShowThresholdSettings(!showThresholdSettings)}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-[#D3D1CF] hover:bg-[#F4F3F3]"
            >
              <Settings className="w-4 h-4" />
              Threshold Settings
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Threshold Settings Modal */}
        {showThresholdSettings && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="p-6 bg-white border-[#D3D1CF]">
              <h3 className="text-lg font-semibold mb-4">Adjust Comparison Threshold</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Threshold: {threshold.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0.01"
                    max="0.5"
                    step="0.01"
                    value={threshold}
                    onChange={(e) => setThreshold(parseFloat(e.target.value))}
                    className="w-full accent-[#0066FF]"
                  />
                  <div className="flex justify-between text-xs text-[#9B9896] mt-1">
                    <span>More sensitive</span>
                    <span>Less sensitive</span>
                  </div>
                </div>
                <p className="text-sm text-[#9B9896]">
                  Lower values detect more subtle differences. Higher values only show major differences.
                </p>
                <div className="flex gap-2">
                  <Button 
                    onClick={handleThresholdChange}
                    disabled={isLoading}
                    className="flex-1 bg-[#0066FF] hover:bg-[#0052CC] text-white"
                  >
                    Apply
                  </Button>
                  <Button 
                    onClick={() => setShowThresholdSettings(false)}
                    variant="outline"
                    className="flex-1 border-[#D3D1CF] hover:bg-[#F4F3F3]"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Video Players - Larger */}
          <div className="lg:col-span-3 space-y-4">
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white rounded-lg p-4 shadow-sm border border-[#D3D1CF]">
                <h3 className="text-sm font-medium mb-3 text-[#9B9896]">{video1Data.filename}</h3>
                <video
                  ref={video1Ref}
                  src={`${API_BASE_URL}/serve-video/${video1Data.video_id}`}
                  className="w-full rounded shadow-sm"
                  onTimeUpdate={handleTimeUpdate}
                  controls={false}
                />
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm border border-[#D3D1CF]">
                <h3 className="text-sm font-medium mb-3 text-[#9B9896]">{video2Data.filename}</h3>
                <video
                  ref={video2Ref}
                  src={`${API_BASE_URL}/serve-video/${video2Data.video_id}`}
                  className="w-full rounded shadow-sm"
                  controls={false}
                />
              </div>
            </div>

            {/* Video Controls */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-[#D3D1CF]">
              <div className="flex items-center gap-4 mb-3">
                <Button
                  onClick={handlePlayPause}
                  size="sm"
                  className="bg-[#0066FF] hover:bg-[#0052CC] text-white"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </Button>
                <span className="text-sm font-medium text-[#1D1C1B]">
                  {formatTime(currentTime)} / {formatTime(video1Data.duration)}
                </span>
              </div>

              {/* Timeline with Markers */}
              <div className="relative space-y-2">
                {/* Difference visualization bar */}
                <div className="relative h-8 bg-[#F4F3F3] rounded overflow-hidden">
                  {differences.map((diff, index) => {
                    const startPercent = (diff.start_sec / video1Data.duration) * 100;
                    const widthPercent = ((diff.end_sec - diff.start_sec) / video1Data.duration) * 100;
                    const isFullVideo = diff.start_sec === 0 && diff.end_sec >= video1Data.duration - 1;
                    
                    return (
                      <div
                        key={index}
                        className={`absolute h-full ${getSeverityColor(diff.distance, isFullVideo)} opacity-70 hover:opacity-100 transition-opacity cursor-pointer`}
                        style={{ 
                          left: `${startPercent}%`,
                          width: `${Math.max(1, widthPercent)}%`
                        }}
                        title={`${formatTime(diff.start_sec)} - ${formatTime(diff.end_sec)}: Distance ${diff.distance.toFixed(3)}`}
                        onClick={() => seekToTime(diff.start_sec)}
                      />
                    );
                  })}
                  
                  {/* Grid lines for time reference */}
                  {Array.from({ length: 5 }, (_, i) => (
                    <div
                      key={i}
                      className="absolute top-0 h-full w-px bg-[#D3D1CF] opacity-30"
                      style={{ left: `${(i + 1) * 20}%` }}
                    />
                  ))}
                </div>
                
                {/* Main playback track */}
                <div className="relative h-3 bg-[#E5E5E5] rounded-full cursor-pointer group"
                     onClick={(e) => {
                       const rect = e.currentTarget.getBoundingClientRect();
                       const percent = (e.clientX - rect.left) / rect.width;
                       seekToTime(percent * video1Data.duration);
                     }}>
                  {/* Progress bar */}
                  <div 
                    className="absolute h-full bg-[#0066FF] rounded-full transition-all duration-100"
                    style={{ width: `${(currentTime / video1Data.duration) * 100}%` }}
                  />
                  
                  {/* Hover indicator */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="h-full bg-white/10 rounded-full" />
                  </div>
                  
                  {/* Current time indicator */}
                  <div 
                    className="absolute w-5 h-5 bg-white border-[3px] border-[#0066FF] rounded-full -translate-x-1/2 -translate-y-1/2 top-1/2 shadow-lg transition-all duration-100 z-10 hover:scale-110"
                    style={{ left: `${(currentTime / video1Data.duration) * 100}%` }}
                  />
                </div>
                
                {/* Time labels */}
                <div className="flex justify-between text-xs text-[#9B9896] select-none">
                  <span>0:00</span>
                  <span>{formatTime(video1Data.duration / 2)}</span>
                  <span>{formatTime(video1Data.duration)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Differences List - Narrower */}
          <div className="lg:col-span-1">
            <Card className="p-4 bg-white border-[#D3D1CF] h-full">
              <h2 className="text-lg font-semibold mb-4">
                Detected Differences ({differences.length})
              </h2>
              
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0066FF]"></div>
                </div>
              ) : (
                <>
                  <div className="space-y-2 max-h-[400px] overflow-y-auto mb-4">
                    {differences.length === 0 ? (
                      <p className="text-[#9B9896] text-center py-8">
                        No significant differences found
                      </p>
                    ) : (
                      differences.map((diff, index) => {
                        const isFullVideo = diff.start_sec === 0 && diff.end_sec >= video1Data.duration - 1;
                        
                        return (
                          <div
                            key={index}
                            className={`p-3 rounded-lg cursor-pointer transition-colors ${
                              isFullVideo 
                                ? 'bg-[#E5E5E5] hover:bg-[#D3D1CF] border border-[#D3D1CF]' 
                                : 'bg-[#F4F3F3] hover:bg-[#D3D1CF]'
                            }`}
                            onClick={() => seekToTime(diff.start_sec)}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">
                                {formatTime(diff.start_sec)} - {formatTime(diff.end_sec)}
                              </span>
                              <Badge className={`${getSeverityColor(diff.distance, isFullVideo)} text-white text-xs`}>
                                {diff.distance === Infinity ? 'Missing' : diff.distance.toFixed(3)}
                              </Badge>
                            </div>
                            {isFullVideo && (
                              <div className="mt-1 text-xs text-[#9B9896]">Overall comparison</div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>

                  {/* Summary */}
                  <div className="pt-4 border-t border-[#D3D1CF]">
                    <div className="text-sm space-y-1">
                      <p className="flex justify-between">
                        <span className="text-[#9B9896]">Total segments:</span>
                        <span className="font-medium">{totalSegments}</span>
                      </p>
                      <p className="flex justify-between">
                        <span className="text-[#9B9896]">Different segments:</span>
                        <span className="font-medium">
                          {differences.filter(d => !(d.start_sec === 0 && d.end_sec >= (video1Data?.duration || 0) - 1)).length}
                        </span>
                      </p>
                      <p className="flex justify-between">
                        <span className="text-[#9B9896]">Similarity:</span>
                        <span className="font-medium text-[#00CC88]">{similarityPercent}%</span>
                      </p>
                      <p className="flex justify-between">
                        <span className="text-[#9B9896]">Threshold:</span>
                        <span className="font-medium">{threshold.toFixed(2)}</span>
                      </p>
                    </div>
                  </div>
                </>
              )}
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}