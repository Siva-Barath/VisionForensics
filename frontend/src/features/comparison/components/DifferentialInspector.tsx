import React, { useState } from 'react';
import {
  ListFilter,
  Type,
  Copy,
  Layers,
  AlertCircle,
  Hash,
} from 'lucide-react';
import type { DifferentialRegion } from '@/types';

interface Props {
  regions: DifferentialRegion[];
  selectedRegionId: string | null;
  onRegionSelect: (region: DifferentialRegion | null) => void;
  onRegionHover: (regionId: string | null) => void;
}

export const DifferentialInspector: React.FC<Props> = ({
  regions,
  selectedRegionId,
  onRegionSelect,
  onRegionHover,
}) => {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const categories = [
    { key: 'ALL', label: `All (${regions.length})` },
    {
      key: 'TEXT_MODIFICATION',
      label: `Text (${regions.filter((r) => r.category === 'TEXT_MODIFICATION').length})`,
    },
    {
      key: 'CONTENT_INSERTION_OR_DELETION',
      label: `Edits (${regions.filter((r) => r.category === 'CONTENT_INSERTION_OR_DELETION').length})`,
    },
    {
      key: 'MACRO_CONTENT_DIFFERENCE',
      label: `Macro (${regions.filter((r) => r.category === 'MACRO_CONTENT_DIFFERENCE').length})`,
    },
  ];

  const filteredRegions = regions.filter((r) =>
    filterCategory === 'ALL' ? true : r.category === filterCategory
  );

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'TEXT_MODIFICATION':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/60">
            <Type size={11} /> Text Mod
          </span>
        );
      case 'MACRO_CONTENT_DIFFERENCE':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/60">
            <Layers size={11} /> Macro Diff
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-red-950/60 text-red-300 border border-red-800/60">
            <Copy size={11} /> Edit / Insert
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-full bg-ink-panel border-l border-ink-border overflow-hidden">
      {/* Header */}
      <div className="p-3 border-b border-ink-border">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ListFilter size={15} className="text-brand" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-white">
              Differential Regions ({regions.length})
            </h3>
          </div>
        </div>

        {/* Category Filter Chips */}
        <div className="flex flex-wrap gap-1">
          {categories.map((c) => (
            <button
              key={c.key}
              onClick={() => setFilterCategory(c.key)}
              className={`text-[11px] font-mono px-2 py-0.5 rounded transition-colors ${
                filterCategory === c.key
                  ? 'bg-brand text-white font-semibold'
                  : 'bg-ink-bg text-gray-400 hover:text-gray-200 border border-ink-border'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Region List */}
      <div className="flex-1 overflow-y-auto divide-y divide-ink-border p-1 space-y-1">
        {filteredRegions.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center text-gray-500">
            <AlertCircle size={28} className="text-gray-600 mb-2" />
            <p className="text-xs font-medium text-gray-400">No Differential Regions Found</p>
            <p className="text-[11px] text-gray-500 mt-1">
              Documents appear visually identical or no discrepancies meet the detection threshold.
            </p>
          </div>
        ) : (
          filteredRegions.map((region) => {
            const isSelected = selectedRegionId === region.region_id;

            return (
              <div
                key={region.region_id}
                onClick={() => onRegionSelect(isSelected ? null : region)}
                onMouseEnter={() => onRegionHover(region.region_id)}
                onMouseLeave={() => onRegionHover(null)}
                className={`p-2.5 rounded cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-brand/20 border border-brand/60'
                    : 'hover:bg-ink-hover border border-transparent'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-xs font-bold text-white flex items-center gap-1">
                    <Hash size={12} className="text-gray-400" />
                    {region.region_id}
                  </span>
                  {getCategoryBadge(region.category)}
                </div>

                {/* Severity & Metrics */}
                <div className="space-y-1.5 text-[11px] font-mono">
                  <div className="flex items-center justify-between text-gray-400">
                    <span>Discrepancy Severity:</span>
                    <span className="text-white font-semibold">{Math.round(region.severity * 100)}%</span>
                  </div>
                  <div className="w-full bg-ink-bg rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        region.severity > 0.7
                          ? 'bg-red-500'
                          : region.severity > 0.4
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.round(region.severity * 100)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-gray-400 pt-1">
                    <span>Area:</span>
                    <span className="text-gray-300">{region.area.toLocaleString()} px²</span>
                  </div>

                  <div className="flex items-center justify-between text-gray-400">
                    <span>BBox:</span>
                    <span className="text-gray-300">
                      [{region.bounding_box.x}, {region.bounding_box.y}, {region.bounding_box.width}×
                      {region.bounding_box.height}]
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
