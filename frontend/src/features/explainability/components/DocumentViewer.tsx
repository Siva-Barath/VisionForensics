import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, AlertCircle, ShieldAlert, CheckCircle2, ChevronLeft, ChevronRight, FileText, Flame } from 'lucide-react';
import { Region } from '../types';
import type { PageDimension } from '@/types';

interface DocumentDimensions {
  width: number;
  height: number;
  page_count?: number;
  pages?: PageDimension[];
}

interface Props {
  imageUrl: string | null;
  heatmapUrl?: string | null;
  regions: Region[];
  imageDimensions?: DocumentDimensions | null;
  selectedRegionId: string | null;
  hoveredRegionId: string | null;
  onRegionSelected: (region: Region | null) => void;
  onRegionHovered: (regionId: string | null) => void;
  isPdf?: boolean;
  originalFilename?: string;
  currentPage?: number;
  pageCount?: number;
  onPageChange?: (newPage: number) => void;
}

export const DocumentViewer: React.FC<Props> = ({
  imageUrl,
  heatmapUrl,
  regions,
  imageDimensions,
  selectedRegionId,
  hoveredRegionId,
  onRegionSelected,
  onRegionHovered,
  isPdf = false,
  originalFilename,
  currentPage = 0,
  pageCount = 1,
  onPageChange,
}) => {
  const [scale, setScale] = useState(1);
  const [heatmapError, setHeatmapError] = useState(false);
  useEffect(() => { setHeatmapError(false); setShowHeatmap(false); }, [heatmapUrl]);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [naturalSize, setNaturalSize] = useState<{ width: number; height: number } | null>(null);
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Reset image loaded/error when imageUrl changes (e.g. on page change)
  useEffect(() => {
    setImageError(false);
    setImageLoaded(false);
  }, [imageUrl]);

  const handleZoomIn = () => setScale((s) => Math.min(Math.round((s + 0.25) * 100) / 100, 3));
  const handleZoomOut = () => setScale((s) => Math.max(Math.round((s - 0.25) * 100) / 100, 0.25));
  const handleResetZoom = () => setScale(1);

  // Filter regions strictly for the currently displayed page
  const visibleRegions = regions.filter((r) => (r.page_index ?? 0) === currentPage);

  // Authoritative coordinate dimensions for current page
  const activePageDim = imageDimensions?.pages?.find((p) => p.page_index === currentPage);
  const docWidth = activePageDim?.width || (currentPage === 0 ? imageDimensions?.width : 0) || naturalSize?.width || 800;
  const docHeight = activePageDim?.height || (currentPage === 0 ? imageDimensions?.height : 0) || naturalSize?.height || 1000;

  // Maximum initial container display width
  const baseDisplayWidth = 720;
  const aspectRatio = docHeight / (docWidth || 1);
  const displayWidth = baseDisplayWidth;
  const displayHeight = Math.round(baseDisplayWidth * aspectRatio);

  const getRegionFill = (sev: number, isSelected: boolean, isHovered: boolean) => {
    if (isSelected) return 'rgba(239, 68, 68, 0.45)';
    if (isHovered) return 'rgba(245, 158, 11, 0.45)';
    if (sev >= 70) return 'rgba(239, 68, 68, 0.25)';
    if (sev >= 30) return 'rgba(245, 158, 11, 0.25)';
    return 'rgba(16, 185, 129, 0.25)';
  };

  const getRegionStroke = (sev: number, isSelected: boolean, isHovered: boolean) => {
    if (isSelected) return '#ef4444';
    if (isHovered) return '#fbbf24';
    if (sev >= 70) return '#ef4444';
    if (sev >= 30) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="bg-ink-panel rounded-sm shadow-md flex flex-col h-[740px] border border-ink-border overflow-hidden">
      {/* Viewer Toolbar */}
      <div className="bg-ink-base border-b border-ink-border px-4 py-2.5 flex flex-wrap justify-between items-center gap-3 z-10">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono font-bold text-gray-200 uppercase tracking-wider">
            Canvas {docWidth > 0 && `(${docWidth} × ${docHeight} px)`}
          </span>
          {visibleRegions.length > 0 ? (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded-sm bg-severity-critical/15 text-severity-critical border border-severity-critical/30 flex items-center gap-1">
              <ShieldAlert size={12} /> {visibleRegions.length} region{visibleRegions.length > 1 ? 's' : ''} on Page {currentPage + 1}
            </span>
          ) : (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded-sm bg-severity-low/15 text-severity-low border border-severity-low/30 flex items-center gap-1">
              <CheckCircle2 size={12} /> No regions flagged (Page {currentPage + 1})
            </span>
          )}
        </div>

        {/* Page Switcher & Zoom Controls */}
        <div className="flex items-center gap-3">
          {/* Multi-Page Navigation Controls */}
          {pageCount > 1 && (
            <div className="flex items-center gap-1 bg-ink-panel px-2 py-1 rounded-sm border border-ink-border">
              <button
                onClick={() => onPageChange?.(Math.max(0, currentPage - 1))}
                disabled={currentPage <= 0}
                className="p-1 hover:bg-ink-hover disabled:opacity-30 disabled:hover:bg-transparent rounded-sm text-gray-300 transition-colors"
                title="Previous Page"
                aria-label="Previous Page"
              >
                <ChevronLeft size={14} />
              </button>
              <span className="text-xs font-mono font-bold text-gray-200 px-2 min-w-[75px] text-center select-none">
                Page {currentPage + 1} of {pageCount}
              </span>
              <button
                onClick={() => onPageChange?.(Math.min(pageCount - 1, currentPage + 1))}
                disabled={currentPage >= pageCount - 1}
                className="p-1 hover:bg-ink-hover disabled:opacity-30 disabled:hover:bg-transparent rounded-sm text-gray-300 transition-colors"
                title="Next Page"
                aria-label="Next Page"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          )}

          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleZoomOut}
              className="p-1.5 bg-ink-panel hover:bg-ink-hover border border-ink-border rounded-sm text-gray-300 transition-colors"
              title="Zoom Out"
              aria-label="Zoom Out"
            >
              <ZoomOut size={14} />
            </button>
            <span className="px-2 font-mono text-xs text-gray-300 min-w-[50px] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1.5 bg-ink-panel hover:bg-ink-hover border border-ink-border rounded-sm text-gray-300 transition-colors"
              title="Zoom In"
              aria-label="Zoom In"
            >
              <ZoomIn size={14} />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1.5 bg-ink-panel hover:bg-ink-hover border border-ink-border rounded-sm text-gray-300 transition-colors ml-1"
              title="Reset Zoom"
              aria-label="Reset Zoom"
            >
              <RotateCcw size={14} />
            </button>
          </div>

          {/* Stored ELA Map Toggle */}
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            disabled={!heatmapUrl || heatmapError}
            className={`px-2.5 py-1 text-xs font-semibold rounded-sm border flex items-center gap-1.5 transition-colors ${
              showHeatmap
                ? 'bg-amber-500 text-black border-amber-400 font-bold shadow-sm'
                : 'bg-ink-panel hover:bg-ink-hover text-gray-300 border-ink-border'
            }`}
            title={heatmapUrl ? "Toggle derived ELA error map" : "No stored ELA map for this page"}
            aria-pressed={showHeatmap}
          >
            <Flame size={13} className={showHeatmap ? 'text-black' : 'text-amber-400'} />
            <span>{showHeatmap ? 'Heatmap: ON' : 'Heatmap: OFF'}</span>
          </button>
        </div>
      </div>

      {/* PDF Exhibit Multi-Page Active Banner */}
      {isPdf && (
        <div className="bg-brand/10 border-b border-brand/30 px-4 py-1.5 text-xs font-mono text-brand flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText size={14} className="shrink-0" />
            <span>
              PDF Exhibit Investigation: Page {currentPage + 1} of {pageCount} ({visibleRegions.length} finding{visibleRegions.length === 1 ? '' : 's'} on this page)
            </span>
          </div>
          {pageCount > 1 && (
            <span className="text-[11px] text-gray-300 hidden sm:inline">
              Use toolbar arrows or select page from inspector
            </span>
          )}
        </div>
      )}

      {/* Interactive Canvas Viewport */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto p-6 flex items-start justify-center bg-[#0d1117]/80 cursor-grab active:cursor-grabbing"
        onClick={(e) => {
          if (e.target === e.currentTarget) onRegionSelected(null);
        }}
      >
        {imageError || !imageUrl ? (
          <div className="m-auto text-center p-8 max-w-md border border-dashed border-ink-border rounded-sm bg-ink-base/50 space-y-3">
            <AlertCircle size={32} className="mx-auto text-severity-high opacity-70" />
            <h4 className="text-sm font-bold text-gray-200">Document Image Preview</h4>
            <p className="text-xs text-muted font-sans leading-relaxed">
              Unable to display preview directly from current browser session.
            </p>
            {originalFilename && (
              <p className="text-[11px] font-mono text-brand bg-ink-base p-2 border border-ink-border rounded-sm">
                Exhibit: {originalFilename} (Page {currentPage + 1})
              </p>
            )}
            <div className="pt-2">
              <button
                onClick={() => {
                  setImageError(false);
                  setImageLoaded(false);
                }}
                className="px-4 py-1.5 bg-brand hover:bg-brand-hover text-white text-xs font-semibold rounded-sm inline-flex items-center gap-1.5"
              >
                <RotateCcw size={13} /> Retry Loading Image
              </button>
            </div>
          </div>
        ) : (
          <div
            className="relative shadow-2xl transition-all duration-150 origin-top bg-ink-base border border-ink-border"
            style={{
              width: `${displayWidth * scale}px`,
              height: `${displayHeight * scale}px`,
            }}
            onClick={(e) => {
              if (e.target === e.currentTarget) onRegionSelected(null);
            }}
          >
            {/* Real Document Image */}
            <img
              src={imageUrl}
              alt={originalFilename ? `${originalFilename} - Page ${currentPage + 1}` : 'Document Exhibit'}
              className={`w-full h-full object-fill block pointer-events-none select-none transition-opacity duration-300 ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              onLoad={(e) => {
                setNaturalSize({
                  width: e.currentTarget.naturalWidth,
                  height: e.currentTarget.naturalHeight,
                });
                setImageLoaded(true);
                setImageError(false);
              }}
              onError={() => setImageError(true)}
            />

            {/* Loading Indicator */}
            {!imageLoaded && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-ink-base/80 space-y-2">
                <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin"></div>
                <span className="text-xs font-mono text-muted uppercase">Rendering Page {currentPage + 1} Canvas...</span>
              </div>
            )}

            {imageLoaded && showHeatmap && heatmapUrl && !heatmapError && (
              <img src={heatmapUrl} alt="Derived normalized ELA error map" className="absolute inset-0 w-full h-full opacity-75 pointer-events-none" onError={() => { setHeatmapError(true); setShowHeatmap(false); }} />
            )}
            {heatmapError && <div role="status" className="absolute top-2 left-2 bg-ink-base p-2 text-xs text-amber-300">Stored ELA map could not be loaded.</div>}
            {showHeatmap && !heatmapError && <div className="absolute top-2 right-2 bg-ink-base/95 p-2 text-[10px] z-20 text-gray-200">Normalized ELA error · dark to yellow · not a risk probability</div>}

            {/* SVG Genuine Evidence Overlays Filtered Strictly to Current Page */}
            {imageLoaded && (
              <svg
                viewBox={`0 0 ${docWidth} ${docHeight}`}
                preserveAspectRatio="none"
                className="absolute inset-0 w-full h-full pointer-events-none"
              >
                {visibleRegions.map((r) => {
                  if (!r.points || r.points.length === 0) return null;
                  const isSelected = r.id === selectedRegionId;
                  const isHovered = r.id === hoveredRegionId;
                  const pts = r.points.map((p) => `${p[0]},${p[1]}`).join(' ');

                  // Compute bounding center for tooltip placement
                  const xs = r.points.map((p) => p[0]);
                  const ys = r.points.map((p) => p[1]);
                  const minX = Math.min(...xs);
                  const minY = Math.min(...ys);

                  return (
                    <g key={r.id} className="pointer-events-auto">
                      <polygon
                        points={pts}
                        fill={getRegionFill(r.severity, isSelected, isHovered)}
                        stroke={getRegionStroke(r.severity, isSelected, isHovered)}
                        strokeWidth={isSelected ? 4 : isHovered ? 3 : 2}
                        strokeDasharray={isSelected ? '6,3' : 'none'}
                        className="cursor-pointer transition-all duration-150 hover:opacity-90"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRegionSelected(isSelected ? null : r);
                        }}
                        onMouseEnter={() => onRegionHovered(r.id)}
                        onMouseLeave={() => onRegionHovered(null)}
                      />

                      {/* Floating Indicator Label on Hover / Select */}
                      {(isSelected || isHovered) && (
                        <g transform={`translate(${minX}, ${Math.max(16, minY - 8)})`}>
                          <rect
                            x={0}
                            y={-16}
                            width={Math.max(90, (r.type.length + 8) * 8)}
                            height={18}
                            fill="#161b22"
                            stroke={isSelected ? '#ef4444' : '#fbbf24'}
                            strokeWidth={1}
                            rx={2}
                            opacity={0.95}
                          />
                          <text
                            x={4}
                            y={-4}
                            fill="#ffffff"
                            fontSize={11}
                            fontFamily="monospace"
                            fontWeight="bold"
                          >
                            {r.type} ({r.severity.toFixed(0)})
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}
              </svg>
            )}
          </div>
        )}
      </div>

      {/* Footer Info Bar */}
      <div className="bg-ink-base border-t border-ink-border px-4 py-2 flex justify-between items-center text-[11px] font-mono text-muted">
        <span>
          Coordinate System: 0,0 Top-Left (Page {currentPage + 1} of {pageCount} • {docWidth} × {docHeight} px)
        </span>
        <span>
          {selectedRegionId
            ? `Selected: ${selectedRegionId}`
            : 'Click highlighted region to inspect details'}
        </span>
      </div>
    </div>
  );
};
