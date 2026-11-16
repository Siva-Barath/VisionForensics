import React from 'react';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Link2,
  Unlink,
  Columns,
  Flame,
  Layers,
  Binary,
  ArrowLeftRight,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import type { ComparisonAlignment } from '@/types';

export type ViewMode = 'side-by-side' | 'diff-heatmap' | 'aligned-overlay' | 'diff-mask';

interface Props {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  scale: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  isSynchronized: boolean;
  onToggleSync: () => void;
  alignment: ComparisonAlignment;
  onSwapDocuments?: () => void;
  overlayOpacity: number;
  onOverlayOpacityChange: (opacity: number) => void;
}

export const ComparisonToolbar: React.FC<Props> = ({
  viewMode,
  onViewModeChange,
  scale,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  isSynchronized,
  onToggleSync,
  alignment,
  onSwapDocuments,
  overlayOpacity,
  onOverlayOpacityChange,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-ink-panel border-b border-ink-border text-sm">
      {/* View Mode Selector */}
      <div className="flex items-center bg-ink-bg rounded-lg p-0.5 border border-ink-border">
        <button
          onClick={() => onViewModeChange('side-by-side')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            viewMode === 'side-by-side'
              ? 'bg-brand text-white shadow-sm'
              : 'text-gray-400 hover:text-gray-200'
          }`}
          title="Side-by-side synchronized view"
        >
          <Columns size={14} />
          <span>Side-by-Side</span>
        </button>

        <button
          onClick={() => onViewModeChange('diff-heatmap')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            viewMode === 'diff-heatmap'
              ? 'bg-brand text-white shadow-sm'
              : 'text-gray-400 hover:text-gray-200'
          }`}
          title="Differential Heatmap overlay"
        >
          <Flame size={14} />
          <span>Diff Heatmap</span>
        </button>

        <button
          onClick={() => onViewModeChange('aligned-overlay')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            viewMode === 'aligned-overlay'
              ? 'bg-brand text-white shadow-sm'
              : 'text-gray-400 hover:text-gray-200'
          }`}
          title="Aligned Overlay comparison"
        >
          <Layers size={14} />
          <span>Aligned Overlay</span>
        </button>

        <button
          onClick={() => onViewModeChange('diff-mask')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            viewMode === 'diff-mask'
              ? 'bg-brand text-white shadow-sm'
              : 'text-gray-400 hover:text-gray-200'
          }`}
          title="Thresholded binary difference mask"
        >
          <Binary size={14} />
          <span>Binary Mask</span>
        </button>
      </div>

      {/* Opacity slider for aligned overlay mode */}
      {viewMode === 'aligned-overlay' && (
        <div className="flex items-center gap-2 px-3 py-1 bg-ink-bg border border-ink-border rounded-lg text-xs">
          <span className="text-gray-400 font-mono">Doc B Opacity:</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={overlayOpacity}
            onChange={(e) => onOverlayOpacityChange(parseFloat(e.target.value))}
            className="w-24 accent-brand cursor-pointer"
          />
          <span className="text-white font-mono w-8">{Math.round(overlayOpacity * 100)}%</span>
        </div>
      )}

      {/* Alignment Status Pill */}
      <div className="flex items-center gap-2">
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono border ${
            alignment.status === 'FEATURE_ALIGNED'
              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
              : 'bg-amber-950/40 text-amber-300 border-amber-800/60'
          }`}
          title={`Status: ${alignment.status} | Matches: ${alignment.matches_found} | Confidence: ${Math.round(
            alignment.confidence * 100
          )}%`}
        >
          {alignment.status === 'FEATURE_ALIGNED' ? (
            <ShieldCheck size={14} className="text-emerald-400" />
          ) : (
            <AlertTriangle size={14} className="text-amber-400" />
          )}
          <span>
            {alignment.status === 'FEATURE_ALIGNED' ? 'ORB Aligned' : 'Direct Resized'} (
            {Math.round(alignment.confidence * 100)}%)
          </span>
        </div>

        {onSwapDocuments && (
          <button
            onClick={onSwapDocuments}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-ink-bg hover:bg-ink-hover text-gray-300 hover:text-white rounded border border-ink-border text-xs transition-colors"
            title="Swap Document A and Document B roles"
          >
            <ArrowLeftRight size={13} />
            <span>Swap A/B</span>
          </button>
        )}
      </div>

      {/* Zoom and Synchronization Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleSync}
          className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
            isSynchronized
              ? 'bg-brand/20 text-brand border-brand/50'
              : 'bg-ink-bg text-gray-400 border-ink-border hover:text-gray-200'
          }`}
          title={isSynchronized ? 'Synchronized Pan & Zoom active' : 'Independent navigation'}
        >
          {isSynchronized ? <Link2 size={13} /> : <Unlink size={13} />}
          <span>{isSynchronized ? 'Sync On' : 'Sync Off'}</span>
        </button>

        <div className="flex items-center bg-ink-bg border border-ink-border rounded-lg p-0.5">
          <button
            onClick={onZoomOut}
            className="p-1 hover:bg-ink-hover rounded text-gray-400 hover:text-gray-200 transition-colors"
            title="Zoom out (-)"
          >
            <ZoomOut size={14} />
          </button>
          <span className="px-2 text-xs font-mono text-gray-300 min-w-[42px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={onZoomIn}
            className="p-1 hover:bg-ink-hover rounded text-gray-400 hover:text-gray-200 transition-colors"
            title="Zoom in (+)"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={onResetZoom}
            className="p-1 hover:bg-ink-hover rounded text-gray-400 hover:text-gray-200 transition-colors ml-0.5 border-l border-ink-border"
            title="Reset zoom to 100%"
          >
            <RotateCcw size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};
