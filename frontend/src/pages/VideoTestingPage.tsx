// AquaGuard AI - Video Testing Page (Phase 9)
// Drag-and-drop video upload, AI processing queue, and HTML5 video streaming player
import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Upload, Film, Play, Trash2, RefreshCw, AlertCircle, CheckCircle2,
  Clock, Cpu, Eye, Layers
} from 'lucide-react';
import { videoAPI } from '../services/api';
import type { VideoItem } from '../types';

export default function VideoTestingPage() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [autoProcess, setAutoProcess] = useState(true);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<number | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchVideos = useCallback(async () => {
    try {
      const res = await videoAPI.list();
      const list: VideoItem[] = res.data ?? [];
      setVideos(list);
      // If currently selected video is updated in the list, update it
      if (selectedVideo) {
        const found = list.find((v) => v.id === selectedVideo.id);
        if (found) setSelectedVideo(found);
      } else if (list.length > 0) {
        setSelectedVideo(list[0]);
      }
    } catch {
      setError('Unable to reach video API. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  }, [selectedVideo]);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  // Polling loop when any video is processing
  useEffect(() => {
    const hasProcessing = videos.some((v) => v.status === 'processing');
    if (hasProcessing) {
      pollTimerRef.current = setInterval(() => {
        fetchVideos();
      }, 1500);
    } else if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [videos, fetchVideos]);

  const handleFileUpload = async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!['.mp4', '.avi', '.mov', '.mkv'].includes(ext)) {
      setError(`Unsupported format: ${ext}. Supported: MP4, AVI, MOV, MKV`);
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await videoAPI.upload(file, autoProcess, (pct) => {
        setUploadProgress(pct);
      });
      setSuccessMsg(`"${file.name}" uploaded successfully!`);
      await fetchVideos();
      if (res.data) {
        setSelectedVideo(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setError(`Upload failed: ${msg}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleProcessVideo = async (id: number) => {
    setProcessingId(id);
    setError(null);
    try {
      await videoAPI.process(id);
      setSuccessMsg('Processing pipeline started in background.');
      await fetchVideos();
    } catch {
      setError('Failed to trigger video processing.');
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteVideo = async (id: number) => {
    if (!confirm('Are you sure you want to delete this video?')) return;
    try {
      await videoAPI.delete(id);
      if (selectedVideo?.id === id) {
        setSelectedVideo(null);
      }
      await fetchVideos();
      setSuccessMsg('Video deleted successfully.');
    } catch {
      setError('Failed to delete video.');
    }
  };

  const completedCount = videos.filter((v) => v.status === 'completed').length;
  const processingCount = videos.filter((v) => v.status === 'processing').length;

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Film size={20} className="text-cyan-400" /> Video Ingestion & AI Testing
          </h1>
          <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
            Upload test pool footage, execute YOLOv8 + ByteTrack + LSTM, and inspect drowning detections
          </p>
        </div>
        <button
          onClick={() => fetchVideos()}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-300 hover:text-white transition-colors"
          style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.5)' }}
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div
          className="p-3 rounded-xl flex items-center gap-3 text-xs"
          style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)', color: '#fca5a5' }}
        >
          <AlertCircle size={16} className="text-red-400 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-white">✕</button>
        </div>
      )}
      {successMsg && (
        <div
          className="p-3 rounded-xl flex items-center gap-3 text-xs"
          style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.4)', color: '#86efac' }}
        >
          <CheckCircle2 size={16} className="text-green-400 flex-shrink-0" />
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="ml-auto text-green-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div
          className="p-3.5 rounded-xl flex items-center gap-3"
          style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
        >
          <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-cyan-500/10 text-cyan-400">
            <Film size={20} />
          </div>
          <div>
            <div className="text-xs" style={{ color: '#64748b' }}>Total Videos</div>
            <div className="text-lg font-bold text-white">{videos.length}</div>
          </div>
        </div>

        <div
          className="p-3.5 rounded-xl flex items-center gap-3"
          style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
        >
          <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-green-500/10 text-green-400">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <div className="text-xs" style={{ color: '#64748b' }}>Analyzed</div>
            <div className="text-lg font-bold text-white">{completedCount}</div>
          </div>
        </div>

        <div
          className="p-3.5 rounded-xl flex items-center gap-3"
          style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
        >
          <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-amber-500/10 text-amber-400">
            <Clock size={20} />
          </div>
          <div>
            <div className="text-xs" style={{ color: '#64748b' }}>Processing</div>
            <div className="text-lg font-bold text-white">{processingCount}</div>
          </div>
        </div>

        <div
          className="p-3.5 rounded-xl flex items-center gap-3"
          style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
        >
          <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-purple-500/10 text-purple-400">
            <Cpu size={20} />
          </div>
          <div>
            <div className="text-xs" style={{ color: '#64748b' }}>Pipeline Model</div>
            <div className="text-xs font-bold text-purple-300">YOLOv8 + LSTM</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Upload & Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Drag & Drop Upload Zone + Video Queue */}
        <div className="lg:col-span-5 space-y-4">
          {/* Upload Dropzone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`p-6 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-200 text-center flex flex-col items-center justify-center ${
              dragOver
                ? 'border-cyan-400 bg-cyan-950/20'
                : 'border-slate-700 hover:border-cyan-500/50 bg-slate-900/40'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".mp4,.avi,.mov,.mkv"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
            />
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-cyan-500/10 text-cyan-400 mb-3">
              <Upload size={24} />
            </div>
            <p className="text-sm font-semibold text-white">Click or drag video file here</p>
            <p className="text-xs mt-1" style={{ color: '#64748b' }}>
              Supports MP4, AVI, MOV, MKV (up to 500 MB)
            </p>

            {/* Auto-process toggle */}
            <div
              onClick={(e) => e.stopPropagation()}
              className="mt-4 flex items-center gap-2 text-xs"
              style={{ color: '#94a3b8' }}
            >
              <input
                type="checkbox"
                id="autoProcessToggle"
                checked={autoProcess}
                onChange={(e) => setAutoProcess(e.target.checked)}
                className="rounded accent-cyan-400 cursor-pointer"
              />
              <label htmlFor="autoProcessToggle" className="cursor-pointer">
                Automatically execute AI detection pipeline on upload
              </label>
            </div>

            {/* Upload progress */}
            {uploading && (
              <div className="w-full mt-4 space-y-1.5">
                <div className="flex justify-between text-xs font-medium text-cyan-400">
                  <span>Uploading video...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full h-2 rounded-full overflow-hidden bg-slate-800">
                  <div
                    className="h-full bg-cyan-400 transition-all duration-200"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Videos Queue List */}
          <div
            className="rounded-2xl p-4 space-y-3"
            style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
          >
            <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: 'rgba(51,65,85,0.4)' }}>
              <div className="flex items-center gap-2">
                <Layers size={16} className="text-cyan-400" />
                <h2 className="text-sm font-bold text-white">Ingested Footage Queue</h2>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                {videos.length} items
              </span>
            </div>

            {videos.length === 0 ? (
              <div className="text-center py-8 text-xs" style={{ color: '#64748b' }}>
                No video files uploaded yet. Drop a test clip above.
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {videos.map((vid) => {
                  const isSelected = selectedVideo?.id === vid.id;
                  const isProc = vid.status === 'processing';
                  const isDone = vid.status === 'completed';

                  return (
                    <div
                      key={vid.id}
                      onClick={() => setSelectedVideo(vid)}
                      className={`p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                        isSelected
                          ? 'bg-cyan-950/30 border border-cyan-500/50 shadow-lg shadow-cyan-950/20'
                          : 'bg-slate-900/40 border border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2 overflow-hidden mr-2">
                          <Film size={14} className={isSelected ? 'text-cyan-400' : 'text-slate-400'} />
                          <span className="text-xs font-semibold text-white truncate">
                            {vid.original_filename}
                          </span>
                        </div>
                        <span
                          className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
                          style={{
                            background:
                              isDone ? 'rgba(34,197,94,0.15)' :
                              isProc ? 'rgba(245,158,11,0.15)' :
                              vid.status === 'failed' ? 'rgba(239,68,68,0.15)' : 'rgba(51,65,85,0.4)',
                            color:
                              isDone ? '#22c55e' :
                              isProc ? '#f59e0b' :
                              vid.status === 'failed' ? '#ef4444' : '#94a3b8',
                          }}
                        >
                          {vid.status}
                        </span>
                      </div>

                      {/* Video specs & progress */}
                      <div className="flex items-center justify-between text-[11px]" style={{ color: '#64748b' }}>
                        <span>
                          {vid.duration_seconds ? `${vid.duration_seconds.toFixed(1)}s` : 'N/A'} • {vid.fps ? `${vid.fps} FPS` : ''}
                        </span>
                        <span>
                          {vid.processed_frames}/{vid.total_frames || 0} frames
                        </span>
                      </div>

                      {/* Mini progress bar if processing */}
                      {isProc && (
                        <div className="w-full mt-2 space-y-1">
                          <div className="w-full h-1.5 rounded-full overflow-hidden bg-slate-800">
                            <div
                              className="h-full bg-amber-400 transition-all duration-300"
                              style={{ width: `${vid.progress_percent}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-[10px] text-amber-400">
                            <span>Inference Running...</span>
                            <span>{vid.progress_percent}%</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Active Video Player & Surveillance Inspector */}
        <div className="lg:col-span-7 space-y-4">
          <div
            className="rounded-2xl p-4 space-y-4"
            style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.5)' }}
          >
            {selectedVideo ? (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                      <Play size={16} className="text-cyan-400" />
                      {selectedVideo.original_filename}
                    </h2>
                    <p className="text-xs" style={{ color: '#64748b' }}>
                      UID: {selectedVideo.video_uid.slice(0, 8)}... • Uploaded {new Date(selectedVideo.uploaded_at).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedVideo.status !== 'processing' && (
                      <button
                        onClick={() => handleProcessVideo(selectedVideo.id)}
                        disabled={processingId === selectedVideo.id}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 hover:bg-cyan-500/30 transition-colors"
                      >
                        <Cpu size={12} className={processingId === selectedVideo.id ? 'animate-spin' : ''} />
                        {selectedVideo.status === 'completed' ? 'Re-run AI' : 'Run Detection'}
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteVideo(selectedVideo.id)}
                      className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 transition-colors"
                      title="Delete video"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>

                {/* HTML5 Video Streaming Container */}
                <div className="relative rounded-xl overflow-hidden bg-black aspect-video border border-slate-800 flex items-center justify-center">
                  <video
                    key={selectedVideo.id}
                    controls
                    autoPlay
                    loop
                    className="w-full h-full object-contain"
                    src={videoAPI.getStreamUrl(selectedVideo.id)}
                  >
                    Your browser does not support the video tag.
                  </video>

                  {/* On-screen status badge */}
                  <div className="absolute top-3 right-3 flex items-center gap-2 pointer-events-none">
                    <span
                      className="px-2.5 py-1 rounded-full text-xs font-bold backdrop-blur-md"
                      style={{
                        background:
                          selectedVideo.status === 'completed' ? 'rgba(34,197,94,0.85)' :
                          selectedVideo.status === 'processing' ? 'rgba(245,158,11,0.85)' :
                          selectedVideo.status === 'failed' ? 'rgba(239,68,68,0.85)' : 'rgba(15,23,42,0.85)',
                        color: '#fff',
                      }}
                    >
                      {selectedVideo.status === 'completed' ? 'AI ANNOTATED STREAM' : selectedVideo.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Processing status bar if in progress */}
                {selectedVideo.status === 'processing' && (
                  <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-amber-400">
                      <span className="flex items-center gap-1.5">
                        <Clock size={14} className="animate-spin" />
                        AI Pipeline In Progress: Tracking &amp; Behavior Scoring
                      </span>
                      <span>{selectedVideo.progress_percent}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full overflow-hidden bg-slate-800">
                      <div
                        className="h-full bg-amber-400 transition-all duration-300"
                        style={{ width: `${selectedVideo.progress_percent}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px]" style={{ color: '#94a3b8' }}>
                      <span>Processed {selectedVideo.processed_frames} of {selectedVideo.total_frames || 'N/A'} frames</span>
                      <span>Est. 30 FPS inference</span>
                    </div>
                  </div>
                )}

                {/* Technical Metadata Matrix */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[11px]" style={{ color: '#64748b' }}>Resolution</span>
                    <p className="font-semibold text-white mt-0.5">
                      {selectedVideo.resolution_width && selectedVideo.resolution_height
                        ? `${selectedVideo.resolution_width}x${selectedVideo.resolution_height}`
                        : 'Auto-detect'}
                    </p>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[11px]" style={{ color: '#64748b' }}>Framerate</span>
                    <p className="font-semibold text-white mt-0.5">
                      {selectedVideo.fps ? `${selectedVideo.fps} FPS` : '30 FPS'}
                    </p>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[11px]" style={{ color: '#64748b' }}>Duration</span>
                    <p className="font-semibold text-white mt-0.5">
                      {selectedVideo.duration_seconds ? `${selectedVideo.duration_seconds.toFixed(1)}s` : 'N/A'}
                    </p>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                    <span className="text-[11px]" style={{ color: '#64748b' }}>File Size</span>
                    <p className="font-semibold text-white mt-0.5">
                      {(selectedVideo.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                {/* Pipeline Diagnostics details */}
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 text-xs space-y-1.5">
                  <p className="font-semibold text-slate-300 flex items-center gap-1.5">
                    <Eye size={13} className="text-cyan-400" /> Pipeline Verification Notes
                  </p>
                  <p style={{ color: '#94a3b8' }}>
                    Videos uploaded with auto-process execute ByteTrack tracker association across all swimmer detections.
                    Bounding boxes rendered in <span className="text-green-400 font-semibold">Green</span> indicate horizontal swimming posture,
                    while <span className="text-red-400 font-semibold">Red</span> signals high drowning risk with vertical distress index $w/h &lt; 0.6$.
                  </p>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Film size={40} className="text-slate-600 mb-3" />
                <p className="text-sm font-semibold text-white">No Video Selected</p>
                <p className="text-xs mt-1" style={{ color: '#64748b' }}>
                  Choose a video from the queue or upload test surveillance footage
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

