import React, { useState, useRef, useEffect } from 'react';
import {
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { DifferentialRegion } from '@/types';
import type { ViewMode } from './ComparisonToolbar';

interface Props {
  docAUrl: string;
  docBUrl: string;
  alignedBUrl?: string;
  diffHeatmapUrl?: string;
  diffMaskUrl?: string;
  regions: DifferentialRegion[];
  selectedRegionId: string | null;
  hoveredRegionId: string | null;
  onRegionSelect: (region: DifferentialRegion | null) => void;
  onRegionHover: (regionId: string | null) => void;
  viewMode: ViewMode;
  scale: number;
  isSynchronized: boolean;
  overlayOpacity: number;
  docADims: [number, number];
  docBDims: [number, number];
  docAName: string;
  docBName: string;
  pageA: number;
  pageB: number;
  pageCountA: number;
  pageCountB: number;
  onPageAChange: (newPage: number) => void;
  onPageBChange: (newPage: number) => void;
}

export const SynchronizedDualViewer: React.FC<Props> = ({
  docAUrl,
  docBUrl,
  alignedBUrl,
  diffHeatmapUrl,
  diffMaskUrl,
  regions,
  selectedRegionId,
  hoveredRegionId,
  onRegionSelect,
  onRegionHover,
  viewMode,
  scale,
  isSynchronized,
  overlayOpacity,
  docADims,
  docBDims,
  docAName,
  docBName,
  pageA,
  pageB,
  pageCountA,
  pageCountB,
  onPageAChange,
  onPageBChange,
}) => {
  // Shared synchronized pan offsets
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [panB, setPanB] = useState({ x: 0, y: 0 }); // independent pan if unsynced
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0, initPanX: 0, initPanY: 0, activeTarget: 'A' });

  const [wA, hA] = docADims.length === 2 && docADims[0] > 0 ? docADims : [800, 1000];
  const [wB, hB] = docBDims.length === 2 && docBDims[0] > 0 ? docBDims : [800, 1000];

  // Reset pan when documents or pages change
  useEffect(() => {
    setPan({ x: 0, y: 0 });
    setPanB({ x: 0, y: 0 });
  }, [docAUrl, docBUrl, pageA, pageB]);

  const handleMouseDown = (e: React.MouseEvent, target: 'A' | 'B') => {
    e.preventDefault();
    setIsDragging(true);
    const initialPan = !isSynchronized && target === 'B' ? panB : pan;
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      initPanX: initialPan.x,
      initPanY: initialPan.y,
      activeTarget: target,
    };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    const nextPan = {
      x: dragStartRef.current.initPanX + dx,
      y: dragStartRef.current.initPanY + dy,
    };

    if (isSynchronized) {
      setPan(nextPan);
      setPanB(nextPan);
    } else {
      if (dragStartRef.current.activeTarget === 'A') {
        setPan(nextPan);
      } else {
        setPanB(nextPan);
      }
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'TEXT_MODIFICATION':
        return { stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.22)' }; // Amber
      case 'MACRO_CONTENT_DIFFERENCE':
        return { stroke: '#a855f7', fill: 'rgba(168, 85, 247, 0.25)' }; // Purple
      default:
        return { stroke: '#ef4444', fill: 'rgba(239, 68, 68, 0.25)' }; // Red
    }
  };

  const renderSvgOverlay = (targetDims: [number, number], isReference: boolean) => {
    const [viewW, viewH] = targetDims;
    return (
      <svg
        viewBox={`0 0 ${viewW} ${viewH}`}
        className="absolute inset-0 w-full h-full pointer-events-none"
      >
        {regions.map((region) => {
          const isSelected = selectedRegionId === region.region_id;
          const isHovered = hoveredRegionId === region.region_id;
          const colors = getCategoryColor(region.category);

          // If region has polygon points, draw polygon; otherwise bounding box
          const pointsStr =
            region.polygon && region.polygon.length >= 3
              ? region.polygon.map((p) => `${p[0]},${p[1]}`).join(' ')
              : null;

          return (
            <g
              key={region.region_id}
              className="pointer-events-auto cursor-pointer transition-all duration-150"
              onClick={(e) => {
                e.stopPropagation();
                onRegionSelect(isSelected ? null : region);
              }}
              onMouseEnter={() => onRegionHover(region.region_id)}
              onMouseLeave={() => onRegionHover(null)}
            >
              {pointsStr ? (
                <polygon
                  points={pointsStr}
                  fill={isSelected ? 'rgba(59, 130, 246, 0.35)' : isHovered ? colors.fill : colors.fill}
                  stroke={isSelected ? '#3b82f6' : isHovered ? '#ffffff' : colors.stroke}
                  strokeWidth={isSelected ? 3.5 : isHovered ? 2.5 : 1.75}
                  strokeDasharray={isReference ? undefined : '4 2'}
                />
              ) : (
                <rect
                  x={region.bounding_box.x}
                  y={region.bounding_box.y}
                  width={region.bounding_box.width}
                  height={region.bounding_box.height}
                  fill={isSelected ? 'rgba(59, 130, 246, 0.35)' : isHovered ? colors.fill : colors.fill}
                  stroke={isSelected ? '#3b82f6' : isHovered ? '#ffffff' : colors.stroke}
                  strokeWidth={isSelected ? 3.5 : isHovered ? 2.5 : 1.75}
                  strokeDasharray={isReference ? undefined : '4 2'}
                />
              )}

              {/* Severity / Region tag badge */}
              {(isSelected || isHovered) && (
                <g transform={`translate(${region.bounding_box.x}, ${Math.max(16, region.bounding_box.y - 6)})`}>
                  <rect
                    x={0}
                    y={-14}
                    width={80}
                    height={16}
                    rx={3}
                    fill="#0f172a"
                    stroke={isSelected ? '#3b82f6' : colors.stroke}
                    strokeWidth={1}
                  />
                  <text
                    x={40}
                    y={-3}
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize={9.5}
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    {region.region_id} ({Math.round(region.severity * 100)}%)
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>
    );
  };

  return (
    <div
      className="flex-1 flex flex-col bg-ink-bg select-none overflow-hidden"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* SIDE-BY-SIDE MODE */}
      {viewMode === 'side-by-side' && (
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-ink-border overflow-hidden">
          {/* Document A (Reference Exhibit) */}
          <div className="flex flex-col h-full overflow-hidden bg-ink-bg relative">
            {/* Header Pill */}
            <div className="flex items-center justify-between px-3 py-2 bg-ink-panel/90 border-b border-ink-border z-10 text-xs">
              <div className="flex items-center gap-2 truncate">
                <span className="px-1.5 py-0.5 rounded font-mono font-bold bg-blue-950/80 text-blue-400 border border-blue-800/60">
                  DOC A (Reference)
                </span>
                <span className="text-gray-200 font-mono truncate" title={docAName}>
                  {docAName}
                </span>
              </div>

              {pageCountA > 1 && (
                <div className="flex items-center gap-1 bg-ink-bg border border-ink-border rounded px-1 py-0.5">
                  <button
                    disabled={pageA <= 0}
                    onClick={() => onPageAChange(pageA - 1)}
                    className="p-0.5 text-gray-400 hover:text-white disabled:opacity-30 disabled:hover:text-gray-400"
                  >
                    <ChevronLeft size={13} />
                  </button>
                  <span className="font-mono text-gray-300 text-[11px] px-1">
                    Pg {pageA + 1}/{pageCountA}
                  </span>
                  <button
                    disabled={pageA >= pageCountA - 1}
                    onClick={() => onPageAChange(pageA + 1)}
                    className="p-0.5 text-gray-400 hover:text-white disabled:opacity-30 disabled:hover:text-gray-400"
                  >
                    <ChevronRight size={13} />
                  </button>
                </div>
              )}
            </div>

            {/* Viewport Canvas A */}
            <div
              className={`flex-1 flex items-center justify-center p-4 overflow-hidden ${
                isDragging ? 'cursor-grabbing' : 'cursor-grab'
              }`}
              onMouseDown={(e) => handleMouseDown(e, 'A')}
            >
              <div
                className="relative shadow-2xl transition-transform duration-75 origin-center"
                style={{
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                  width: `${wA}px`,
                  maxWidth: '90%',
                  aspectRatio: `${wA} / ${hA}`,
                }}
              >
                <img
                  src={docAUrl}
                  alt="Document A"
                  className="w-full h-full object-contain rounded border border-ink-border bg-white"
                  draggable={false}
                />
                {renderSvgOverlay([wA, hA], true)}
              </div>
            </div>
          </div>

          {/* Document B (Comparison Exhibit) */}
          <div className="flex flex-col h-full overflow-hidden bg-ink-bg relative">
            {/* Header Pill */}
            <div className="flex items-center justify-between px-3 py-2 bg-ink-panel/90 border-b border-ink-border z-10 text-xs">
              <div className="flex items-center gap-2 truncate">
                <span className="px-1.5 py-0.5 rounded font-mono font-bold bg-amber-950/80 text-amber-400 border border-amber-800/60">
                  DOC B (Comparison)
                </span>
                <span className="text-gray-200 font-mono truncate" title={docBName}>
                  {docBName}
                </span>
              </div>

              {pageCountB > 1 && (
                <div className="flex items-center gap-1 bg-ink-bg border border-ink-border rounded px-1 py-0.5">
                  <button
                    disabled={pageB <= 0}
                    onClick={() => onPageBChange(pageB - 1)}
                    className="p-0.5 text-gray-400 hover:text-white disabled:opacity-30 disabled:hover:text-gray-400"
                  >
                    <ChevronLeft size={13} />
                  </button>
                  <span className="font-mono text-gray-300 text-[11px] px-1">
                    Pg {pageB + 1}/{pageCountB}
                  </span>
                  <button
                    disabled={pageB >= pageCountB - 1}
                    onClick={() => onPageBChange(pageB + 1)}
                    className="p-0.5 text-gray-400 hover:text-white disabled:opacity-30 disabled:hover:text-gray-400"
                  >
                    <ChevronRight size={13} />
                  </button>
                </div>
              )}
            </div>

            {/* Viewport Canvas B */}
            <div
              className={`flex-1 flex items-center justify-center p-4 overflow-hidden ${
                isDragging ? 'cursor-grabbing' : 'cursor-grab'
              }`}
              onMouseDown={(e) => handleMouseDown(e, 'B')}
            >
              <div
                className="relative shadow-2xl transition-transform duration-75 origin-center"
                style={{
                  transform: `translate(${isSynchronized ? pan.x : panB.x}px, ${
                    isSynchronized ? pan.y : panB.y
                  }px) scale(${scale})`,
                  width: `${wB}px`,
                  maxWidth: '90%',
                  aspectRatio: `${wB} / ${hB}`,
                }}
              >
                <img
                  src={docBUrl}
                  alt="Document B"
                  className="w-full h-full object-contain rounded border border-ink-border bg-white"
                  draggable={false}
                />
                {renderSvgOverlay([wA, hA], false)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DIFFERENTIAL HEATMAP MODE */}
      {viewMode === 'diff-heatmap' && (
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-ink-bg relative">
          <div className="flex items-center justify-between px-4 py-2 bg-ink-panel border-b border-ink-border text-xs">
            <span className="text-gray-300 font-mono">
              Composite Differential Heatmap (Jet Colormap: Blue = Exact Match, Red/Yellow = Local Alteration)
            </span>
            <span className="text-gray-400 font-mono text-[11px]">
              Altered Regions: {regions.length} detected
            </span>
          </div>

          <div
            className={`flex-1 flex items-center justify-center p-4 overflow-hidden ${
              isDragging ? 'cursor-grabbing' : 'cursor-grab'
            }`}
            onMouseDown={(e) => handleMouseDown(e, 'A')}
          >
            <div
              className="relative shadow-2xl transition-transform duration-75 origin-center"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                width: `${wA}px`,
                maxWidth: '90%',
                aspectRatio: `${wA} / ${hA}`,
              }}
            >
              <img
                src={diffHeatmapUrl || docAUrl}
                alt="Differential Heatmap"
                className="w-full h-full object-contain rounded border border-ink-border bg-ink-panel"
                draggable={false}
              />
              {renderSvgOverlay([wA, hA], true)}
            </div>
          </div>
        </div>
      )}

      {/* ALIGNED OVERLAY MODE */}
      {viewMode === 'aligned-overlay' && (
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-ink-bg relative">
          <div className="flex items-center justify-between px-4 py-2 bg-ink-panel border-b border-ink-border text-xs">
            <span className="text-gray-300 font-mono">
              Aligned Geometric Overlay (Doc A Base + Aligned Doc B Layer at {Math.round(overlayOpacity * 100)}%)
            </span>
            <span className="text-gray-400 font-mono text-[11px]">
              Aligned Dimensions: {wA} x {hA} px
            </span>
          </div>

          <div
            className={`flex-1 flex items-center justify-center p-4 overflow-hidden ${
              isDragging ? 'cursor-grabbing' : 'cursor-grab'
            }`}
            onMouseDown={(e) => handleMouseDown(e, 'A')}
          >
            <div
              className="relative shadow-2xl transition-transform duration-75 origin-center"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                width: `${wA}px`,
                maxWidth: '90%',
                aspectRatio: `${wA} / ${hA}`,
              }}
            >
              {/* Base Document A */}
              <img
                src={docAUrl}
                alt="Document A Base"
                className="w-full h-full object-contain rounded border border-ink-border bg-white"
                draggable={false}
              />
              {/* Aligned Document B Layer with Opacity */}
              <img
                src={alignedBUrl || docBUrl}
                alt="Aligned Document B Overlay"
                className="absolute inset-0 w-full h-full object-contain rounded"
                style={{ opacity: overlayOpacity }}
                draggable={false}
              />
              {renderSvgOverlay([wA, hA], true)}
            </div>
          </div>
        </div>
      )}

      {/* BINARY DIFFERENCE MASK MODE */}
      {viewMode === 'diff-mask' && (
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-ink-bg relative">
          <div className="flex items-center justify-between px-4 py-2 bg-ink-panel border-b border-ink-border text-xs">
            <span className="text-gray-300 font-mono">
              Thresholded Binary Differential Mask (White = Altered Pixels, Black = Identical)
            </span>
            <span className="text-gray-400 font-mono text-[11px]">
              Threshold: T=28 | Morphological Close (5x5)
            </span>
          </div>

          <div
            className={`flex-1 flex items-center justify-center p-4 overflow-hidden ${
              isDragging ? 'cursor-grabbing' : 'cursor-grab'
            }`}
            onMouseDown={(e) => handleMouseDown(e, 'A')}
          >
            <div
              className="relative shadow-2xl transition-transform duration-75 origin-center"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                width: `${wA}px`,
                maxWidth: '90%',
                aspectRatio: `${wA} / ${hA}`,
              }}
            >
              <img
                src={diffMaskUrl || docAUrl}
                alt="Differential Binary Mask"
                className="w-full h-full object-contain rounded border border-ink-border bg-black"
                draggable={false}
              />
              {renderSvgOverlay([wA, hA], true)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
