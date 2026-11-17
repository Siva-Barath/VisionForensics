import React, { useState } from 'react';
import { 
  Image as ImageIcon, 
  Minus, 
  Plus, 
  Activity, 
  ChevronLeft, 
  ChevronRight,
  RotateCcw
} from 'lucide-react';
import { Region } from '../types';

interface Props {
  imageUrl: string | null;
  heatmapUrl?: string | null;
  regions: Region[];
  currentPage?: number;
  pageCount?: number;
  onPageChange?: (page: number) => void;
  originalFilename?: string;
}

export const DocumentPreviewCard: React.FC<Props> = ({
  imageUrl,
  heatmapUrl,
  regions,
  currentPage = 0,
  pageCount = 1,
  onPageChange,
  originalFilename,
}) => {
  const [scale, setScale] = useState(1);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleZoomIn = () => setScale((s) => Math.min(Math.round((s + 0.2) * 10) / 10, 2.5));
  const handleZoomOut = () => setScale((s) => Math.max(Math.round((s - 0.2) * 10) / 10, 0.6));
  const handleResetZoom = () => setScale(1);

  // Filter regions for the current page
  const visibleRegions = regions.filter((r) => (r.page_index ?? 0) === currentPage);

  return (
    <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-4 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-[#E6E5F0]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
            <ImageIcon size={18} />
          </div>
          <h2 className="text-sm font-bold text-[#17172F]">Document Preview</h2>
        </div>

        {/* Multi-page Switcher if applicable */}
        {pageCount > 1 && (
          <div className="flex items-center gap-1.5 bg-[#F8F9FF] border border-[#E6E5F0] px-2 py-1 rounded-lg text-xs font-semibold text-[#17172F]">
            <button
              onClick={() => onPageChange?.(Math.max(0, currentPage - 1))}
              disabled={currentPage <= 0}
              className="p-0.5 hover:text-[#7045E8] disabled:opacity-30 disabled:hover:text-[#17172F]"
              title="Previous Page"
            >
              <ChevronLeft size={14} />
            </button>
            <span className="text-[11px] font-mono min-w-[65px] text-center">
              Page {currentPage + 1} / {pageCount}
            </span>
            <button
              onClick={() => onPageChange?.(Math.min(pageCount - 1, currentPage + 1))}
              disabled={currentPage >= pageCount - 1}
              className="p-0.5 hover:text-[#7045E8] disabled:opacity-30 disabled:hover:text-[#17172F]"
              title="Next Page"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>

      {/* Main Image Viewport */}
      <div className="relative flex-1 min-h-[320px] max-h-[460px] bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl overflow-hidden flex items-center justify-center p-3 select-none">
        {imageUrl && !imageError ? (
          <div
            className="relative transition-transform duration-200 origin-center max-w-full max-h-full flex items-center justify-center"
            style={{ transform: `scale(${scale})` }}
          >
            {/* Base Document Image */}
            <img
              src={imageUrl}
              alt={originalFilename || 'Document Preview'}
              className={`max-h-[380px] max-w-full w-auto h-auto object-contain rounded shadow-sm border border-black/5 transition-opacity duration-300 ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />

            {/* Heatmap Overlay if Active */}
            {imageLoaded && showHeatmap && heatmapUrl && (
              <img
                src={heatmapUrl}
                alt="ELA Heatmap Overlay"
                className="absolute inset-0 w-full h-full object-contain opacity-65 mix-blend-multiply pointer-events-none rounded"
              />
            )}

            {/* Suspicious Region Highlights (e.g. Region 1) */}
            {imageLoaded && visibleRegions.length > 0 && (
              <div className="absolute inset-0 pointer-events-none">
                {visibleRegions.map((r, idx) => {
                  if (!r.points || r.points.length < 2) return null;
                  const xs = r.points.map((p) => p[0]);
                  const ys = r.points.map((p) => p[1]);
                  const minX = Math.min(...xs);
                  const maxX = Math.max(...xs);
                  const minY = Math.min(...ys);
                  const maxY = Math.max(...ys);

                  return (
                    <div
                      key={r.id || idx}
                      className="absolute border-2 border-[#E9A12A] bg-[#E9A12A]/15 rounded"
                      style={{
                        left: `${minX}%`,
                        top: `${minY}%`,
                        width: `${Math.max(5, maxX - minX)}%`,
                        height: `${Math.max(5, maxY - minY)}%`,
                      }}
                    >
                      <span className="absolute -top-6 left-0 px-1.5 py-0.5 rounded bg-[#E9A12A] text-white font-mono text-[9px] font-bold shadow-sm whitespace-nowrap">
                        Region {idx + 1} ({r.severity.toFixed(0)})
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Loading Spinner */}
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center text-[#7045E8]">
                <div className="w-8 h-8 border-2 border-[#7045E8] border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>
        ) : (
          <div className="text-center p-6 space-y-2 text-[#73758B]">
            <ImageIcon size={36} className="mx-auto text-slate-300" />
            <p className="text-xs font-semibold text-[#17172F]">Preview Unavailable</p>
            <p className="text-[11px] text-[#73758B]">Document exhibit is retained on disk.</p>
          </div>
        )}
      </div>

      {/* Bottom Controls Bar */}
      <div className="flex items-center justify-between pt-2 border-t border-[#E6E5F0] text-xs">
        {/* Zoom Controls */}
        <div className="flex items-center gap-1.5 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl p-1">
          <button
            type="button"
            onClick={handleZoomOut}
            className="p-1 text-[#73758B] hover:text-[#17172F] hover:bg-white rounded-lg transition-colors"
            title="Zoom Out"
          >
            <Minus size={14} />
          </button>
          <button
            type="button"
            onClick={handleZoomIn}
            className="p-1 text-[#73758B] hover:text-[#17172F] hover:bg-white rounded-lg transition-colors"
            title="Zoom In"
          >
            <Plus size={14} />
          </button>
          <button
            type="button"
            onClick={handleResetZoom}
            className="px-2 py-0.5 font-mono text-[11px] font-bold text-[#17172F] hover:text-[#7045E8] transition-colors"
            title="Reset Zoom"
          >
            {Math.round(scale * 100)}%
          </button>
          <button
            type="button"
            onClick={handleResetZoom}
            className="p-1 text-[#73758B] hover:text-[#7045E8] hover:bg-white rounded-lg transition-colors"
            title="Reset to 100%"
          >
            <RotateCcw size={12} />
          </button>
        </div>

        {/* Heatmap Toggle Switch */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowHeatmap(!showHeatmap)}
            className="flex items-center gap-2 text-xs font-semibold text-[#17172F] select-none group cursor-pointer"
          >
            <Activity size={14} className={showHeatmap ? 'text-[#7045E8]' : 'text-[#73758B]'} />
            <span className={showHeatmap ? 'text-[#7045E8]' : 'text-[#73758B]'}>Heatmap</span>
            {/* iOS-style toggle */}
            <div
              className={`w-9 h-5 rounded-full transition-colors relative p-0.5 ${
                showHeatmap ? 'bg-[#7045E8]' : 'bg-[#DDD5F9]'
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${
                  showHeatmap ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};
