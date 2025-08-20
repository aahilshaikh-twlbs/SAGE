'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
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
  const [video1Url, setVideo1Url] = useState<string>('');
  const [video2Url, setVideo2Url] = useState<string>('');
  const video1Ref = useRef<HTMLVideoElement>(null);
  const video2Ref = useRef<HTMLVideoElement>(null);
  
  // OpenAI Analysis state
  const [openaiAnalysis, setOpenaiAnalysis] = useState<string>('');
  const [keyInsights, setKeyInsights] = useState<string[]>([]);
  const [timeSegments, setTimeSegments] = useState<string[]>([]);
  const [isGeneratingAnalysis, setIsGeneratingAnalysis] = useState(false);
  const [hasOpenAIKey, setHasOpenAIKey] = useState(false);

  const loadComparison = async (video1: VideoData, video2: VideoData, thresholdValue: number) => {
    try {
      setIsLoading(true);
      setError(null);
      const comparison = await api.compareVideos(
        video1.embedding_id,
        video2.embedding_id,
        thresholdValue,
        'cosine'
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

  const generateOpenAIAnalysis = async () => {
    if (!video1Data || !video2Data || differences.length === 0) return;
    
    try {
      setIsGeneratingAnalysis(true);
      setError(null);
      
      const analysis = await api.generateOpenAIAnalysis(
        video1Data.embedding_id,
        video2Data.embedding_id,
        differences,
        threshold,
        Math.max(video1Data.duration, video2Data.duration)
      );
      
      setOpenaiAnalysis(analysis.analysis);
      setKeyInsights(analysis.key_insights);
      setTimeSegments(analysis.time_segments);
    } catch (err) {
      console.error('Error generating OpenAI analysis:', err);
      setError('Failed to generate AI analysis. Please check your OpenAI API key.');
    } finally {
      setIsGeneratingAnalysis(false);
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
        
        // Verify videos still exist on backend and get current status
        try {
          const video1Status = await api.getVideoStatus(video1.video_id);
          const video2Status = await api.getVideoStatus(video2.video_id);
          
          // Update video data with current backend status
          const updatedVideo1 = {
            ...video1,
            duration: video1Status.duration || video1.duration,
            status: video1Status.status
          };
          
          const updatedVideo2 = {
            ...video2,
            duration: video2Status.duration || video2.duration,
            status: video2Status.status
          };
          
          setVideo1Data(updatedVideo1);
          setVideo2Data(updatedVideo2);
          
          // Get video URLs for playback
          try {
            const url1 = await api.getVideoUrl(video1.video_id);
            const url2 = await api.getVideoUrl(video2.video_id);
            setVideo1Url(url1);
            setVideo2Url(url2);
          } catch (urlError) {
            console.error('Error getting video URLs:', urlError);
            setError('Failed to load video URLs. Please try again.');
          }
          
          // Load initial comparison
          await loadComparison(updatedVideo1, updatedVideo2, threshold);
          
        } catch (statusError) {
          console.error('Error getting video status:', statusError);
          setError('Failed to get video status. Please check if videos are still available.');
        }
        
      } catch (error) {
        console.error('Error loading data:', error);
        setError('Failed to load video data. Please try again.');
      }
    };
    
    loadData();
  }, []);

  // Check for OpenAI API key
  useEffect(() => {
    const openaiKey = localStorage.getItem('sage_openai_key');
    setHasOpenAIKey(!!openaiKey);
  }, []);

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
    if (video1Ref.current && video2Ref.current && video1Data && video2Data) {
      // Constrain time to the shorter video's duration to prevent out-of-bounds
      const constrainedTime = Math.min(time, Math.min(video1Data.duration, video2Data.duration));
      
      // Pause videos first to ensure seeking works properly
      video1Ref.current.pause();
      video2Ref.current.pause();
      setIsPlaying(false);
      
      // Set the time
      video1Ref.current.currentTime = constrainedTime;
      video2Ref.current.currentTime = constrainedTime;
      setCurrentTime(constrainedTime);
      
      // Resume playback if it was playing
      setTimeout(() => {
        if (isPlaying) {
          video1Ref.current?.play();
          video2Ref.current?.play();
        }
      }, 100);
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
    
    if (distance >= 999999.0) return 'bg-[#DC2626]'; // Dark Red for missing segments
    
    // Cosine distance scale: 0 = identical, 1 = orthogonal, 2 = completely different
    // Colors: Green (similar) -> Yellow -> Orange -> Red (different)
    if (distance >= 1.5) return 'bg-[#DC2626]'; // Dark Red for completely different
    if (distance >= 1.0) return 'bg-[#EF4444]'; // Red for very different (orthogonal+)
    if (distance >= 0.7) return 'bg-[#F97316]'; // Orange for significantly different
    if (distance >= 0.5) return 'bg-[#F59E0B]'; // Amber for moderately different
    if (distance >= 0.3) return 'bg-[#EAB308]'; // Yellow for somewhat different
    if (distance >= 0.1) return 'bg-[#84CC16]'; // Lime for slightly different
    return 'bg-[#06B6D4]'; // Cyan for very similar (close to identical)
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

  // Calculate similarity based on the actual comparison results
  // Use the backend's similarity calculation which is based on segments that are NOT different
  // Only count segments that were actually compared (not the 999999.0 ones)
  const actualDifferences = differences.filter(d => d.distance < 999999.0).length;
  const similarityPercent = totalSegments > 0 
    ? ((totalSegments - actualDifferences) / totalSegments * 100).toFixed(2)
    : '100.00';

  // Use the longer video's duration for timeline
  const maxDuration = Math.max(video1Data.duration, video2Data.duration);
  
  // For very long videos, show segments but make timeline non-clickable to avoid UI clutter
  const isLongVideo = maxDuration > 300; // 5 minutes
  const showSegmentDetails = true; // Always show segments
  const timelineClickable = !isLongVideo; // Only make timeline clickable for shorter videos

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
                {video1Url ? (
                  <video
                    ref={video1Ref}
                    src={video1Url}
                    className="w-full rounded shadow-sm"
                    onTimeUpdate={handleTimeUpdate}
                    controls={false}
                  />
                ) : (
                  <div className="w-full h-48 bg-gray-100 rounded flex items-center justify-center">
                    <div className="text-gray-500">Loading video...</div>
                  </div>
                )}
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm border border-[#D3D1CF]">
                <h3 className="text-sm font-medium mb-3 text-[#9B9896]">{video2Data.filename}</h3>
                {video2Url ? (
                  <video
                    ref={video2Ref}
                    src={video2Url}
                    className="w-full rounded shadow-sm"
                    onTimeUpdate={handleTimeUpdate}
                    controls={false}
                  />
                ) : (
                  <div className="w-full h-48 bg-gray-100 rounded flex items-center justify-center">
                    <div className="text-gray-500">Loading video...</div>
                  </div>
                )}
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
                  {formatTime(currentTime)} / {formatTime(maxDuration)}
                </span>
              </div>

              {/* Timeline with Markers */}
              <div className="relative space-y-2">
                {/* Difference visualization bar */}
                <div className="relative h-8 bg-[#F4F3F3] rounded overflow-hidden border border-[#D3D1CF]">
                  {showSegmentDetails ? (
                    // Show individual segments for shorter videos
                    differences.map((diff, index) => {
                      const startPercent = (diff.start_sec / maxDuration) * 100;
                      const widthPercent = ((diff.end_sec - diff.start_sec) / maxDuration) * 100;
                      const isFullVideo = diff.start_sec === 0 && diff.end_sec >= maxDuration - 1;
                      
                      return (
                        <div
                          key={index}
                          className={`absolute h-full ${getSeverityColor(diff.distance, isFullVideo)} opacity-80 hover:opacity-100 transition-opacity cursor-pointer border border-white/20`}
                          style={{ 
                            left: `${startPercent}%`,
                            width: `${Math.max(1, widthPercent)}%`
                          }}
                          title={`Click to jump to ${formatTime(diff.start_sec)} - ${formatTime(diff.end_sec)} (Distance: ${diff.distance.toFixed(3)})`}
                          onClick={() => seekToTime(diff.start_sec)}
                        />
                      );
                    })
                  ) : (
                    // For long videos, show a summary indicating overall differences
                    <div className="flex items-center justify-center h-full text-sm text-[#9B9896]">
                      {differences.length > 0 ? (
                        <span>Timeline shows {differences.length} detected differences</span>
                      ) : (
                        <span>No differences detected</span>
                      )}
                    </div>
                  )}
                  
                  {/* Grid lines for time reference */}
                  {Array.from({ length: 5 }, (_, i) => (
                    <div
                      key={i}
                      className="absolute top-0 h-full w-px bg-[#D3D1CF] opacity-30"
                      style={{ left: `${(i + 1) * 20}%` }}
                    />
                  ))}
                  
                  {/* Time labels */}
                  <div className="absolute -bottom-6 left-0 right-0 flex justify-between text-xs text-[#9B9896]">
                    <span>0:00</span>
                    <span>{formatTime(maxDuration)}</span>
                  </div>
                </div>
                
                {/* Main playback track */}
                <div className="relative h-3 bg-[#E5E5E5] rounded-full cursor-pointer group"
                     onClick={(e) => {
                       if (timelineClickable) {
                         const rect = e.currentTarget.getBoundingClientRect();
                         const percent = (e.clientX - rect.left) / rect.width;
                         seekToTime(percent * maxDuration);
                       }
                     }}>
                  {/* Progress bar */}
                  <div 
                    className="absolute h-full bg-[#0066FF] rounded-full transition-all duration-100"
                    style={{ width: `${(currentTime / maxDuration) * 100}%` }}
                  />
                  
                  {/* Hover indicator */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="h-full bg-white/10 rounded-full" />
                  </div>
                  
                  {/* Current time indicator */}
                  <div 
                    className="absolute w-5 h-5 bg-white border-[3px] border-[#0066FF] rounded-full -translate-x-1/2 -translate-y-1/2 top-1/2 shadow-lg transition-all duration-100 z-10 hover:scale-110"
                    style={{ left: `${(currentTime / maxDuration) * 100}%` }}
                  />
                </div>
                
                {/* Time labels */}
                <div className="flex justify-between text-xs text-[#9B9896] select-none">
                  <span>0:00</span>
                  <span>{formatTime(maxDuration / 2)}</span>
                  <span>{formatTime(maxDuration)}</span>
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
                      // Show individual segments for shorter videos
                      differences.map((diff, index) => {
                        const isFullVideo = diff.start_sec === 0 && diff.end_sec >= video1Data?.duration - 1;
                        
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
