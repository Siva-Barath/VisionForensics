import React from 'react';
import { ShieldAlert, Crosshair, X } from 'lucide-react';
import { Region } from '../types';

interface Props {
  region: Region | null;
  onClearSelection?: () => void;
}

export const RegionInspector: React.FC<Props> = ({ region, onClearSelection }) => {
  if (!region) {
    return (
      <div className="bg-ink-panel border border-ink-border rounded-sm p-8 text-center text-gray-400 space-y-2">
        <Crosshair size={28} className="mx-auto text-muted opacity-40" />
        <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">No Region Selected</h4>
        <p className="text-xs text-muted font-sans leading-relaxed">
          Click any highlighted region on the document viewer or an evidence item in the explorer to inspect its forensic coordinates and metrics.
        </p>
      </div>
    );
  }

  // Calculate bounding box metrics
  const xs = region.points?.map((p) => p[0]) || [];
  const ys = region.points?.map((p) => p[1]) || [];
  const minX = xs.length > 0 ? Math.min(...xs) : 0;
  const maxX = xs.length > 0 ? Math.max(...xs) : 0;
  const minY = ys.length > 0 ? Math.min(...ys) : 0;
  const maxY = ys.length > 0 ? Math.max(...ys) : 0;
  const width = Math.max(0, maxX - minX);
  const height = Math.max(0, maxY - minY);

  const isHighSeverity = region.severity >= 70;
  const isMediumSeverity = region.severity >= 30;

  const severityBadgeClass = isHighSeverity
    ? 'bg-severity-critical/15 text-severity-critical border-severity-critical/30'
    : isMediumSeverity
    ? 'bg-severity-high/15 text-severity-high border-severity-high/30'
    : 'bg-severity-low/15 text-severity-low border-severity-low/30';

  return (
    <div className="bg-ink-panel border border-ink-border rounded-sm p-5 space-y-5">
      {/* Header */}
      <div className="flex justify-between items-start pb-3 border-b border-ink-border">
        <div>
          <span className="text-[10px] font-mono font-bold text-muted uppercase tracking-widest block">
            Visual Region Inspector
          </span>
          <h3 className="text-sm font-bold text-white font-mono mt-0.5 flex items-center gap-2">
            <Crosshair size={14} className="text-brand" />
            {region.id}
          </h3>
        </div>
        {onClearSelection && (
          <button
            onClick={onClearSelection}
            className="p-1 hover:bg-ink-hover rounded-sm text-muted hover:text-gray-200 transition-colors"
            title="Clear Selection"
            aria-label="Clear Selection"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 text-xs font-mono">
        <div className="bg-ink-base border border-ink-border p-3 rounded-sm">
          <p className="text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Category</p>
          <p className="font-bold text-brand">{region.type}</p>
        </div>

        <div className="bg-ink-base border border-ink-border p-3 rounded-sm">
          <p className="text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Severity</p>
          <span className={`inline-block px-2 py-0.5 rounded-sm font-bold border text-[11px] ${severityBadgeClass}`}>
            {region.severity.toFixed(1)} / 100
          </span>
        </div>

        <div className="bg-ink-base border border-ink-border p-3 rounded-sm">
          <p className="text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Detector</p>
          <p className="text-gray-200 truncate">{region.detector || 'visual_collector'}</p>
        </div>

        <div className="bg-ink-base border border-ink-border p-3 rounded-sm">
          <p className="text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Confidence</p>
          <p className="text-gray-200">{(region.confidence * 100).toFixed(1)}%</p>
        </div>
      </div>

      {/* Forensic Finding Description */}
      <div>
        <p className="text-[10px] font-mono font-bold text-muted uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
          <ShieldAlert size={12} className={isHighSeverity ? 'text-severity-critical' : 'text-severity-high'} />
          Forensic Finding Description
        </p>
        <div className="text-xs text-gray-300 font-sans bg-ink-base border border-ink-border p-3 rounded-sm leading-relaxed">
          {region.description || 'No detailed anomaly description recorded for this region.'}
        </div>
      </div>

      {/* Bounding Box Coordinate Details */}
      <div>
        <p className="text-[10px] font-mono font-bold text-muted uppercase tracking-wider mb-1.5">
          Spatial Bounding Box (Pixels)
        </p>
        <div className="bg-ink-base border border-ink-border p-3 rounded-sm space-y-2 text-xs font-mono">
          <div className="flex justify-between text-gray-300">
            <span className="text-muted">Top-Left:</span>
            <span>[{minX}, {minY}]</span>
          </div>
          <div className="flex justify-between text-gray-300">
            <span className="text-muted">Bottom-Right:</span>
            <span>[{maxX}, {maxY}]</span>
          </div>
          <div className="flex justify-between text-gray-300 pt-1 border-t border-ink-border">
            <span className="text-muted">Region Dimensions:</span>
            <span className="text-brand font-bold">{width} × {height} px</span>
          </div>
        </div>
      </div>

      {/* Polygon Vertices */}
      {region.points && region.points.length > 0 && (
        <div>
          <p className="text-[10px] font-mono font-bold text-muted uppercase tracking-wider mb-1">
            Polygon Vertices ({region.points.length} points)
          </p>
          <p className="text-[11px] font-mono text-muted bg-ink-base border border-ink-border p-2 rounded-sm truncate">
            {region.points.map((p) => `[${p[0]}, ${p[1]}]`).join(' → ')}
          </p>
        </div>
      )}
    </div>
  );
};
