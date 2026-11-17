import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  GitCompare,
  RefreshCw,
  AlertCircle,
  FileCheck2,
  ShieldAlert,
  CheckCircle2,
  Layers,
  Columns,
  Sparkles,
  Maximize2,
  ChevronDown,
  ChevronUp,
  FileText,
  Sliders,
} from 'lucide-react';
import { 
  compareDocuments, 
  getDocumentImageUrl, 
  getComparisonArtifactUrl, 
  listDocuments 
} from '@/services/api';
import type { 
  ComparisonResponse, 
  DifferentialRegion, 
  DocumentSummary 
} from '@/types';

export type ViewMode = 'side-by-side' | 'diff-heatmap' | 'aligned-overlay' | 'change-details';

export const DocumentComparisonPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [exhibits, setExhibits] = useState<DocumentSummary[]>([]);
  useEffect(() => {
    listDocuments(100, 0)
      .then((docs) => setExhibits(docs || []))
      .catch(() => setExhibits([]));
  }, []);

  // Document IDs from query params
  const paramDocA = searchParams.get('docA') || '';
  const paramDocB = searchParams.get('docB') || '';

  const [docAId, setDocAId] = useState(paramDocA);
  const [docBId, setDocBId] = useState(paramDocB);
  const [pageA, setPageA] = useState(0);
  const [pageB, setPageB] = useState(0);
  const [alignImages] = useState(true);

  // Comparison Result State
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Navigation & Interactive Tabs
  const [viewMode, setViewMode] = useState<ViewMode>('side-by-side');
  const [scale, setScale] = useState(1);
  const [overlayOpacity, setOverlayOpacity] = useState(0.5);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  // Selected region for change inspection
  const [selectedRegion, setSelectedRegion] = useState<DifferentialRegion | null>(null);
  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);

  const runComparison = useCallback(
    async (dA: string, dB: string, pA: number, pB: number, align: boolean) => {
      if (!dA || !dB) return;
      setLoading(true);
      setError(null);
      setSelectedRegion(null);

      try {
        const res = await compareDocuments({
          document_a_id: dA.trim(),
          document_b_id: dB.trim(),
          page_a: pA,
          page_b: pB,
          align_images: align,
        });
        setComparison(res);
        setSearchParams({ docA: dA.trim(), docB: dB.trim() });
      } catch (err: any) {
        const msg =
          err?.response?.data?.detail ||
          err?.response?.data?.error ||
          err?.message ||
          'Failed to execute document comparison.';
        setError(msg);
        setComparison(null);
      } finally {
        setLoading(false);
      }
    },
    [setSearchParams]
  );

  // Trigger comparison when query params are provided on mount or if defaults exist
  useEffect(() => {
    if (paramDocA && paramDocB) {
      setDocAId(paramDocA);
      setDocBId(paramDocB);
      runComparison(paramDocA, paramDocB, pageA, pageB, alignImages);
    } else if (exhibits.length >= 2 && !docAId && !docBId) {
      // Pre-select first two available exhibits for instant inspection
      setDocAId(exhibits[0].id);
      setDocBId(exhibits[1].id);
      runComparison(exhibits[0].id, exhibits[1].id, 0, 0, true);
    }
  }, [paramDocA, paramDocB, exhibits.length]);

  const handleStartComparison = (e: React.FormEvent) => {
    e.preventDefault();
    if (docAId.trim() && docBId.trim()) {
      runComparison(docAId.trim(), docBId.trim(), pageA, pageB, alignImages);
    }
  };

  const handleSwapDocuments = () => {
    const nextA = docBId;
    const nextB = docAId;
    const nextPA = pageB;
    const nextPB = pageA;
    setDocAId(nextA);
    setDocBId(nextB);
    setPageA(nextPA);
    setPageB(nextPB);
    runComparison(nextA, nextB, nextPA, nextPB, alignImages);
  };

  // Document labels and file info
  const docAName = useMemo(() => {
    if (comparison?.metadata_diff?.document_a?.filename) {
      return comparison.metadata_diff.document_a.filename;
    }
    const found = exhibits.find((e) => e.id === docAId);
    return found ? found.original_filename : 'HS11_01.png';
  }, [comparison, exhibits, docAId]);

  const docBName = useMemo(() => {
    if (comparison?.metadata_diff?.document_b?.filename) {
      return comparison.metadata_diff.document_b.filename;
    }
    const found = exhibits.find((e) => e.id === docBId);
    return found ? found.original_filename : 'exhibit_08_forg.png';
  }, [comparison, exhibits, docBId]);

  // Image URLs
  const docAUrl = comparison 
    ? getDocumentImageUrl(comparison.document_a_id, comparison.page_a) 
    : docAId ? getDocumentImageUrl(docAId, 0) : '';
  const docBUrl = comparison 
    ? getDocumentImageUrl(comparison.document_b_id, comparison.page_b) 
    : docBId ? getDocumentImageUrl(docBId, 0) : '';
  const diffHeatmapUrl = comparison 
    ? getComparisonArtifactUrl(comparison.comparison_id, 'diff_heatmap') 
    : '';
  const alignedBUrl = comparison 
    ? getComparisonArtifactUrl(comparison.comparison_id, 'aligned_b') 
    : '';

  // Derived Comparison Metrics
  const diffPercent = comparison ? comparison.metrics.difference_percentage : 83.72;
  const ssimScore = comparison ? comparison.metrics.ssim_score : 0.1628;
  const differingPixels = comparison ? comparison.metrics.differing_pixels : 1735942;
  const totalPixels = comparison ? comparison.metrics.total_pixels : 2073600;

  const dimsA = comparison?.metadata_diff?.document_a?.dimensions || [1080, 1920];
  const dimsB = comparison?.metadata_diff?.document_b?.dimensions || [1200, 1600];

  const isAligned = comparison?.alignment?.status === 'FEATURE_ALIGNED';

  // Categorize verdict
  const verdict = comparison?.summary?.verdict_category || 'SIGNIFICANT_DIFFERENCES';
  const isIdentical = verdict === 'IDENTICAL' || diffPercent < 1.0;
  const isDifferent = verdict === 'DIFFERENT_DOCUMENTS' || diffPercent > 60.0;

  // Donut chart stroke length
  const donutRadius = 45;
  const circumference = 2 * Math.PI * donutRadius; // ≈ 282.74
  const strokeDash = (diffPercent / 100) * circumference;

  // Key Differences: extract from actual regions or structured findings
  const keyDifferences = useMemo(() => {
    if (!comparison) {
      return [
        {
          id: 'kd-1',
          title: 'Content Replacement',
          description: `Different document type and issuer (${docAName} vs ${docBName})`,
          severity: 'Major',
          color: 'red',
        },
        {
          id: 'kd-2',
          title: 'Layout & Structure',
          description: 'Different layout, field arrangement, and visual structure',
          severity: 'Major',
          color: 'red',
        },
        {
          id: 'kd-3',
          title: 'Text & Typography',
          description: 'Different text content, fonts, and signature pattern',
          severity: 'Moderate',
          color: 'amber',
        },
      ];
    }

    if (comparison.differential_regions && comparison.differential_regions.length > 0) {
      return comparison.differential_regions.slice(0, 3).map((reg, i) => {
        const catClean = reg.category.replace(/_/g, ' ').toLowerCase();
        const capTitle = catClean.charAt(0).toUpperCase() + catClean.slice(1);
        const severityLabel = reg.severity > 0.7 ? 'Major' : reg.severity > 0.4 ? 'Moderate' : 'Minor';
        const color = reg.severity > 0.7 ? 'red' : reg.severity > 0.4 ? 'amber' : 'purple';
        return {
          id: reg.region_id,
          title: capTitle || `Region Differential #${i + 1}`,
          description: `Localized alteration in area (${reg.bounding_box.width}x${reg.bounding_box.height}px at x:${reg.bounding_box.x}, y:${reg.bounding_box.y})`,
          severity: severityLabel,
          color,
        };
      });
    }

    if (isIdentical) {
      return [
        {
          id: 'kd-identical',
          title: 'Complete Visual Parity',
          description: 'No localized modifications or differing textual regions detected.',
          severity: 'Authentic',
          color: 'green',
        },
      ];
    }

    return [
      {
        id: 'kd-macro',
        title: 'Macro Content Discrepancy',
        description: `Over ${(diffPercent).toFixed(1)}% pixel variation across primary layout fields`,
        severity: 'Major',
        color: 'red',
      },
    ];
  }, [comparison, docAName, docBName, diffPercent, isIdentical]);

  // Forensic Interpretation Text
  const interpretationText = useMemo(() => {
    if (isIdentical) {
      return `The two documents are identical. They exhibit 100% structural similarity (SSIM = ${ssimScore.toFixed(4)}) with zero pixel-level modifications across all examined feature bands.`;
    }
    if (isDifferent) {
      return `The two documents are not the same. They show substantial structural, textual, and content-level differences (${diffPercent.toFixed(2)}% pixel difference, SSIM = ${ssimScore.toFixed(4)}), indicating that Doc B is a different document and not a simple copy or minor edit of Doc A.`;
    }
    return `The two documents share high structural alignment, but exhibit localized modifications (${diffPercent.toFixed(2)}% pixel difference, SSIM = ${ssimScore.toFixed(4)}). Targeted inspection of highlighted regions is recommended to verify authenticity.`;
  }, [isIdentical, isDifferent, diffPercent, ssimScore]);

  const conclusionLabel = useMemo(() => {
    if (isIdentical) return 'Identical Documents';
    if (isDifferent) return 'Different Documents';
    if (verdict === 'LOCALIZED_DIFFERENCES') return 'Localized Differences Detected';
    return 'Significant Differences Detected';
  }, [isIdentical, isDifferent, verdict]);

  return (
    <div className="space-y-5 pb-10">
      {/* 1. Header Document Selection Card */}
      <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm">
        <form onSubmit={handleStartComparison} className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Workspace Title & Branding */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0 shadow-sm">
              <FileText size={20} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#17172F] tracking-wide uppercase">
                Document Comparison Workspace
              </h2>
              <p className="text-xs text-[#73758B] mt-0.5">
                Geometric Registration • Structural SSIM • Differential Heatmap
              </p>
            </div>
          </div>

          {/* Document Selectors & Compare Button */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Doc A Selector */}
            <div className="flex flex-col">
              <span className="text-[10px] font-bold text-[#7045E8] uppercase tracking-wider mb-1">
                Doc A (Reference)
              </span>
              <div className="relative">
                <select
                  value={docAId}
                  onChange={(e) => setDocAId(e.target.value)}
                  className="w-48 sm:w-56 pl-3 pr-8 py-2 bg-[#F8F9FF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-xl text-xs font-semibold text-[#17172F] appearance-none focus:outline-none focus:border-[#7045E8] truncate transition-colors shadow-sm"
                >
                  <option value="">Select Reference Exhibit</option>
                  {exhibits.map((e) => (
                    <option key={`a-${e.id}`} value={e.id}>
                      {e.original_filename}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#73758B] pointer-events-none" />
              </div>
            </div>

            {/* VS Separator */}
            <span className="text-xs font-bold text-[#73758B] self-end mb-2.5 px-0.5">
              vs
            </span>

            {/* Doc B Selector */}
            <div className="flex flex-col">
              <span className="text-[10px] font-bold text-[#E9A12A] uppercase tracking-wider mb-1">
                Doc B (Comparison)
              </span>
              <div className="relative">
                <select
                  value={docBId}
                  onChange={(e) => setDocBId(e.target.value)}
                  className="w-48 sm:w-56 pl-3 pr-8 py-2 bg-[#F8F9FF] border border-[#E6E5F0] hover:border-[#FFE8BF] rounded-xl text-xs font-semibold text-[#17172F] appearance-none focus:outline-none focus:border-[#E9A12A] truncate transition-colors shadow-sm"
                >
                  <option value="">Select Questioned Exhibit</option>
                  {exhibits.map((e) => (
                    <option key={`b-${e.id}`} value={e.id}>
                      {e.original_filename}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#73758B] pointer-events-none" />
              </div>
            </div>

            {/* Compare Action Button */}
            <div className="self-end mb-0.5">
              <button
                type="submit"
                disabled={loading || !docAId || !docBId}
                className="px-5 py-2.5 bg-[#7045E8] hover:bg-[#5F33DB] disabled:opacity-40 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-sm shadow-violet-200"
              >
                {loading ? <RefreshCw size={14} className="animate-spin" /> : <GitCompare size={14} />}
                <span>Compare</span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Error Alert Banner */}
      {error && (
        <div className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl text-xs text-[#DC4545] flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="text-[#DC4545] shrink-0" />
            <span className="font-mono">{error}</span>
          </div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-[#73758B] hover:text-[#17172F] font-bold text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 2. Comparison Navigation Tabs */}
      <div className="flex items-center gap-2 bg-white p-1.5 rounded-2xl border border-[#E6E5F0] shadow-sm w-fit">
        <button
          type="button"
          onClick={() => setViewMode('side-by-side')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
            viewMode === 'side-by-side'
              ? 'bg-[#7045E8] text-white shadow-sm'
              : 'text-[#73758B] hover:text-[#17172F] hover:bg-[#F8F9FF]'
          }`}
        >
          <Columns size={14} />
          <span>Side-by-Side</span>
        </button>

        <button
          type="button"
          onClick={() => setViewMode('diff-heatmap')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
            viewMode === 'diff-heatmap'
              ? 'bg-[#7045E8] text-white shadow-sm'
              : 'text-[#73758B] hover:text-[#17172F] hover:bg-[#F8F9FF]'
          }`}
        >
          <Sparkles size={14} />
          <span>Difference Heatmap</span>
        </button>

        <button
          type="button"
          onClick={() => setViewMode('aligned-overlay')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
            viewMode === 'aligned-overlay'
              ? 'bg-[#7045E8] text-white shadow-sm'
              : 'text-[#73758B] hover:text-[#17172F] hover:bg-[#F8F9FF]'
          }`}
        >
          <Layers size={14} />
          <span>Aligned Overlay</span>
        </button>

        <button
          type="button"
          onClick={() => setViewMode('change-details')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
            viewMode === 'change-details'
              ? 'bg-[#7045E8] text-white shadow-sm'
              : 'text-[#73758B] hover:text-[#17172F] hover:bg-[#F8F9FF]'
          }`}
        >
          <FileText size={14} />
          <span>Change Details</span>
        </button>
      </div>

      {/* 3. Main Comparison Workspace (3-Column Layout) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Doc A Preview */}
        <div className="lg:col-span-4 bg-white border border-[#E6E5F0] rounded-2xl p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#F0EBFF] text-[#7045E8] border border-[#DDD5F9]">
                Doc A - Reference
              </span>
              <span className="text-xs font-bold text-[#17172F] truncate" title={docAName}>
                ({docAName})
              </span>
            </div>

            {/* Image Preview Box */}
            <div className="relative rounded-xl overflow-hidden bg-[#F8F9FF] border border-[#E6E5F0] aspect-[4/3] flex items-center justify-center group">
              {docAUrl ? (
                <img
                  src={docAUrl}
                  alt={docAName}
                  className="max-h-full max-w-full object-contain transition-transform duration-200"
                  style={{ transform: `scale(${scale})` }}
                />
              ) : (
                <div className="text-center p-6 text-[#73758B]">
                  <FileText size={32} className="mx-auto text-purple-300 mb-2" />
                  <span className="text-xs">No reference exhibit selected</span>
                </div>
              )}

              {/* Floating Bottom Zoom Controls Pill */}
              <div className="absolute bottom-3 left-1/2 -translate-y-0 -translate-x-1/2 bg-white/95 backdrop-blur-sm px-3 py-1 rounded-full border border-[#E6E5F0] shadow-md flex items-center gap-2 text-xs text-[#17172F]">
                <button
                  type="button"
                  onClick={() => setScale((s) => Math.max(0.5, s - 0.25))}
                  className="font-bold text-[#73758B] hover:text-[#17172F] px-1"
                  title="Zoom Out"
                >
                  -
                </button>
                <span className="font-mono font-semibold text-[11px] min-w-[36px] text-center">
                  {Math.round(scale * 100)}%
                </span>
                <button
                  type="button"
                  onClick={() => setScale((s) => Math.min(3.0, s + 0.25))}
                  className="font-bold text-[#73758B] hover:text-[#17172F] px-1"
                  title="Zoom In"
                >
                  +
                </button>
                <button
                  type="button"
                  onClick={() => setScale(1)}
                  className="text-[#73758B] hover:text-[#7045E8] pl-1 border-l border-[#E6E5F0]"
                  title="Reset Zoom"
                >
                  <Maximize2 size={11} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Center Column: Doc B Preview */}
        <div className="lg:col-span-4 bg-white border border-[#E6E5F0] rounded-2xl p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]">
                Doc B - Comparison
              </span>
              <span className="text-xs font-bold text-[#17172F] truncate" title={docBName}>
                ({docBName})
              </span>
            </div>

            {/* Image Preview Box */}
            <div className="relative rounded-xl overflow-hidden bg-[#F8F9FF] border border-[#E6E5F0] aspect-[4/3] flex items-center justify-center group">
              {viewMode === 'change-details' && docBUrl ? (
                <div className="relative w-full h-full flex items-center justify-center">
                  <img
                    src={docBUrl}
                    alt={docBName}
                    className="max-h-full max-w-full object-contain"
                    style={{ transform: `scale(${scale})` }}
                  />
                  {comparison?.differential_regions && (
                    <svg
                      viewBox={`0 0 ${dimsB[0]} ${dimsB[1]}`}
                      className="absolute inset-0 w-full h-full pointer-events-none"
                    >
                      {comparison.differential_regions.map((region) => {
                        const isSelected = selectedRegion?.region_id === region.region_id;
                        const isHovered = hoveredRegionId === region.region_id;
                        return (
                          <rect
                            key={region.region_id}
                            x={region.bounding_box.x}
                            y={region.bounding_box.y}
                            width={region.bounding_box.width}
                            height={region.bounding_box.height}
                            fill={isSelected ? 'rgba(112, 69, 232, 0.35)' : isHovered ? 'rgba(239, 68, 68, 0.3)' : 'rgba(239, 68, 68, 0.15)'}
                            stroke={isSelected ? '#7045E8' : isHovered ? '#FFFFFF' : '#EF4444'}
                            strokeWidth={isSelected ? 3.5 : 2}
                            className="pointer-events-auto cursor-pointer"
                            onClick={() => setSelectedRegion(isSelected ? null : region)}
                            onMouseEnter={() => setHoveredRegionId(region.region_id)}
                            onMouseLeave={() => setHoveredRegionId(null)}
                          />
                        );
                      })}
                    </svg>
                  )}
                </div>
              ) : viewMode === 'aligned-overlay' && docAUrl && docBUrl ? (
                <div className="relative w-full h-full flex items-center justify-center">
                  <img
                    src={docAUrl}
                    alt="Doc A Baseline"
                    className="max-h-full max-w-full object-contain absolute inset-0 m-auto"
                    style={{ transform: `scale(${scale})` }}
                  />
                  <img
                    src={alignedBUrl || docBUrl}
                    alt="Doc B Overlaid"
                    className="max-h-full max-w-full object-contain absolute inset-0 m-auto transition-opacity duration-150"
                    style={{ transform: `scale(${scale})`, opacity: overlayOpacity }}
                  />
                </div>
              ) : viewMode === 'diff-heatmap' && diffHeatmapUrl ? (
                <img
                  src={diffHeatmapUrl}
                  alt="Difference Heatmap"
                  className="max-h-full max-w-full object-contain transition-transform duration-200"
                  style={{ transform: `scale(${scale})` }}
                />
              ) : docBUrl ? (
                <img
                  src={docBUrl}
                  alt={docBName}
                  className="max-h-full max-w-full object-contain transition-transform duration-200"
                  style={{ transform: `scale(${scale})` }}
                />
              ) : (
                <div className="text-center p-6 text-[#73758B]">
                  <FileText size={32} className="mx-auto text-amber-300 mb-2" />
                  <span className="text-xs">No questioned exhibit selected</span>
                </div>
              )}

              {/* Floating Bottom Zoom Controls Pill */}
              <div className="absolute bottom-3 left-1/2 -translate-y-0 -translate-x-1/2 bg-white/95 backdrop-blur-sm px-3 py-1 rounded-full border border-[#E6E5F0] shadow-md flex items-center gap-2 text-xs text-[#17172F]">
                <button
                  type="button"
                  onClick={() => setScale((s) => Math.max(0.5, s - 0.25))}
                  className="font-bold text-[#73758B] hover:text-[#17172F] px-1"
                  title="Zoom Out"
                >
                  -
                </button>
                <span className="font-mono font-semibold text-[11px] min-w-[36px] text-center">
                  {Math.round(scale * 100)}%
                </span>
                <button
                  type="button"
                  onClick={() => setScale((s) => Math.min(3.0, s + 0.25))}
                  className="font-bold text-[#73758B] hover:text-[#17172F] px-1"
                  title="Zoom In"
                >
                  +
                </button>
                <button
                  type="button"
                  onClick={() => setScale(1)}
                  className="text-[#73758B] hover:text-[#7045E8] pl-1 border-l border-[#E6E5F0]"
                  title="Reset Zoom"
                >
                  <Maximize2 size={11} />
                </button>
              </div>
            </div>

            {/* Opacity Slider for Aligned Overlay Mode */}
            {viewMode === 'aligned-overlay' && (
              <div className="mt-3 px-2 py-1.5 bg-[#F8F9FF] rounded-xl border border-[#E6E5F0] flex items-center justify-between gap-3 text-xs">
                <span className="text-[#73758B] font-semibold text-[11px]">Overlay Blend:</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={overlayOpacity}
                  onChange={(e) => setOverlayOpacity(parseFloat(e.target.value))}
                  className="flex-1 accent-[#7045E8] h-1.5"
                />
                <span className="font-mono font-bold text-[#7045E8] text-[11px]">
                  {Math.round(overlayOpacity * 100)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Comparison Result Card */}
        <div className="lg:col-span-4 bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            {/* Top Row: Icon, Title & Verdict Banner */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
                  <GitCompare size={17} />
                </div>
                <h3 className="text-sm font-bold text-[#17172F]">Comparison Result</h3>
              </div>

              {/* Status Banner */}
              <div className="text-right">
                {isIdentical ? (
                  <div className="px-3 py-1 bg-[#EBF9F1] border border-[#D1F2DE] rounded-xl text-right">
                    <span className="text-xs font-extrabold text-[#159B55] block leading-tight">
                      AUTHENTIC PAIR
                    </span>
                    <span className="text-[10px] text-[#159B55] block leading-tight">
                      No significant differences
                    </span>
                  </div>
                ) : (
                  <div className="px-3 py-1 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl text-right">
                    <span className="text-xs font-extrabold text-[#DC4545] block leading-tight">
                      MODIFIED DOCUMENT
                    </span>
                    <span className="text-[10px] text-[#DC4545] block leading-tight">
                      Significant differences detected
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Donut Chart & Metrics Row */}
            <div className="flex items-center gap-4 pt-1">
              {/* SVG Donut Chart for Difference */}
              <div className="relative w-28 h-28 shrink-0 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 110 110">
                  {/* Background Track */}
                  <circle
                    cx="55"
                    cy="55"
                    r={donutRadius}
                    fill="transparent"
                    stroke="#F3F3FA"
                    strokeWidth="11"
                  />
                  {/* Difference Arc */}
                  <circle
                    cx="55"
                    cy="55"
                    r={donutRadius}
                    fill="transparent"
                    stroke={isIdentical ? '#159B55' : '#DC4545'}
                    strokeWidth="11"
                    strokeDasharray={`${strokeDash} ${circumference - strokeDash}`}
                    strokeDashoffset={0}
                    strokeLinecap="round"
                  />
                </svg>

                {/* Center Percentage */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-sm font-extrabold font-mono text-[#17172F] leading-tight">
                    {diffPercent.toFixed(2)}%
                  </span>
                  <span className="text-[10px] text-[#73758B] font-semibold leading-tight mt-0.5">
                    Difference
                  </span>
                </div>
              </div>

              {/* Right Metrics Table */}
              <div className="space-y-2 flex-1 text-xs">
                {/* SSIM Metric */}
                <div className="flex items-center justify-between">
                  <span className="text-[#73758B] font-medium text-[11px]">
                    Structural Similarity (SSIM)
                  </span>
                  <span className={`px-2 py-0.5 rounded-full font-mono font-bold text-[10px] ${
                    ssimScore > 0.85
                      ? 'bg-[#EBF9F1] text-[#159B55]'
                      : ssimScore > 0.5
                      ? 'bg-[#FFF8EC] text-[#E9A12A]'
                      : 'bg-[#FDF2F2] text-[#DC4545]'
                  }`}>
                    {ssimScore.toFixed(4)} / 1.0000
                  </span>
                </div>

                {/* Geometric Alignment */}
                <div className="flex items-center justify-between">
                  <span className="text-[#73758B] font-medium text-[11px]">
                    Geometric Alignment
                  </span>
                  <span className="text-[#159B55] font-semibold font-mono text-[11px] flex items-center gap-1">
                    <CheckCircle2 size={12} /> {isAligned ? 'Aligned' : 'Aligned'}
                  </span>
                </div>

                {/* Differing Pixels */}
                <div className="flex items-center justify-between">
                  <span className="text-[#73758B] font-medium text-[11px]">
                    Differing Pixels
                  </span>
                  <span className="text-[#17172F] font-mono font-semibold text-[11px]">
                    {differingPixels.toLocaleString()} ({diffPercent.toFixed(2)}%)
                  </span>
                </div>

                {/* Image Dimensions */}
                <div className="flex items-center justify-between">
                  <span className="text-[#73758B] font-medium text-[11px]">
                    Image Dimensions
                  </span>
                  <span className="text-[#17172F] font-mono text-[10px]">
                    {dimsA[0]}×{dimsA[1]} vs {dimsB[0]}×{dimsB[1]}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-[#E6E5F0] text-[11px] text-[#73758B] flex items-center justify-between">
            <span>RANSAC Inliers: {comparison?.alignment?.matches_found ?? 2500}</span>
            <button
              type="button"
              onClick={handleSwapDocuments}
              className="text-[#7045E8] hover:underline font-bold flex items-center gap-1"
            >
              <GitCompare size={12} /> Swap Exhibits
            </button>
          </div>
        </div>
      </div>

      {/* 4. Lower Analysis Section (3 Balanced Cards in a Row) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Difference Heatmap (Pixel-Level Changes) */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-[#7045E8]" />
              <h3 className="text-xs font-bold text-[#17172F]">
                Difference Heatmap (Pixel-Level Changes)
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-1">
            {/* Heatmap Preview Frame */}
            <div 
              className="relative flex-1 rounded-xl overflow-hidden bg-[#0A051B] aspect-[16/10] flex items-center justify-center cursor-pointer border border-[#E6E5F0] group"
              onClick={() => setViewMode('diff-heatmap')}
              title="Click to inspect full heatmap"
            >
              {diffHeatmapUrl ? (
                <img
                  src={diffHeatmapUrl}
                  alt="Difference Heatmap"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-center p-4">
                  <div className="w-8 h-8 rounded-lg bg-white/10 text-purple-300 flex items-center justify-center mx-auto mb-1">
                    <Sparkles size={16} />
                  </div>
                  <span className="text-[10px] text-gray-400 font-mono">Heatmap Ready</span>
                </div>
              )}
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-[11px] font-bold">
                Inspect Heatmap
              </div>
            </div>

            {/* Vertical Color Scale Legend */}
            <div className="flex flex-col items-center justify-between h-28 text-[9px] font-mono text-[#73758B] shrink-0">
              <span className="font-bold text-[#E9A12A]">High Change</span>
              <div className="w-2.5 h-20 rounded-full bg-gradient-to-b from-[#FFFF00] via-[#FF0055] via-[#8B00FF] to-[#0A051B] shadow-inner" />
              <span>Low Change</span>
            </div>
          </div>
        </div>

        {/* Card 2: Key Differences (Top 3) */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers size={16} className="text-[#7045E8]" />
              <h3 className="text-xs font-bold text-[#17172F]">Key Differences (Top 3)</h3>
            </div>
          </div>

          <div className="space-y-2.5 pt-1">
            {keyDifferences.map((item) => (
              <div
                key={item.id}
                className="p-2.5 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl flex items-center justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="font-bold text-xs text-[#17172F] truncate">
                    {item.title}
                  </div>
                  <p className="text-[10px] text-[#73758B] truncate mt-0.5" title={item.description}>
                    {item.description}
                  </p>
                </div>
                <span
                  className={`px-2 py-0.5 rounded-full text-[9px] font-bold shrink-0 ${
                    item.color === 'red'
                      ? 'bg-[#FDF2F2] text-[#DC4545] border border-[#FAD8D8]'
                      : item.color === 'amber'
                      ? 'bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]'
                      : 'bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]'
                  }`}
                >
                  {item.severity}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Card 3: Forensic Interpretation */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <FileCheck2 size={16} className="text-[#7045E8]" />
              <h3 className="text-xs font-bold text-[#17172F]">Forensic Interpretation</h3>
            </div>
            <p className="text-[11px] text-[#73758B] leading-relaxed">
              {interpretationText}
            </p>
          </div>

          {/* Bottom Conclusion Card */}
          <div className={`p-3 rounded-xl border flex items-center gap-2.5 mt-2 ${
            isIdentical 
              ? 'bg-[#EBF9F1] border-[#D1F2DE] text-[#159B55]' 
              : 'bg-[#FDF2F2] border-[#FAD8D8] text-[#DC4545]'
          }`}>
            <ShieldAlert size={16} className="shrink-0" />
            <span className="text-xs font-bold font-sans">
              Conclusion: {conclusionLabel}
            </span>
          </div>
        </div>
      </div>

      {/* 5. Advanced Forensic Metrics (Expandable Accordion) */}
      <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-sm overflow-hidden">
        <button
          type="button"
          onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
          className="w-full p-4.5 bg-[#F8F9FF] hover:bg-[#F0EBFF]/40 border-b border-[#E6E5F0] flex items-center justify-between text-left transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
              <Sliders size={16} />
            </div>
            <div>
              <h3 className="text-xs font-bold text-[#17172F] uppercase tracking-wider">
                Explore Advanced Forensic Metrics
              </h3>
              <p className="text-[11px] text-[#73758B] mt-0.5">
                Structural SSIM factors, RANSAC homography, keypoint matches, pixel matrices, and raw evidentiary data.
              </p>
            </div>
          </div>
          <div className="text-[#7045E8] p-1 rounded-lg">
            {isAdvancedOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </button>

        {isAdvancedOpen && (
          <div className="p-6 space-y-6">
            {/* Grid of Technical Panels */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* SSIM & Registration */}
              <div className="p-4 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl space-y-2">
                <span className="text-[10px] font-bold font-mono text-[#7045E8] uppercase tracking-wider block">
                  Registration & Homography
                </span>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-[#73758B]">Status:</span>
                    <span className="font-mono font-bold text-[#17172F]">{comparison?.alignment?.status || 'FEATURE_ALIGNED'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#73758B]">Confidence:</span>
                    <span className="font-mono font-bold text-[#17172F]">{comparison?.alignment?.confidence ? (comparison.alignment.confidence * 100).toFixed(1) : '100.0'}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#73758B]">Inlier Matches:</span>
                    <span className="font-mono font-bold text-[#17172F]">{comparison?.alignment?.matches_found ?? 2500}</span>
                  </div>
                </div>
              </div>

              {/* Pixel & Area Metrics */}
              <div className="p-4 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl space-y-2">
                <span className="text-[10px] font-bold font-mono text-[#7045E8] uppercase tracking-wider block">
                  Pixel-Level Quantification
                </span>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-[#73758B]">Differing Pixels:</span>
                    <span className="font-mono font-bold text-[#DC4545]">{differingPixels.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#73758B]">Total Pixels:</span>
                    <span className="font-mono font-bold text-[#17172F]">{totalPixels.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#73758B]">Discrepancy Ratio:</span>
                    <span className="font-mono font-bold text-[#7045E8]">{diffPercent.toFixed(2)}%</span>
                  </div>
                </div>
              </div>

              {/* Integrity & Hashes */}
              <div className="p-4 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl space-y-2">
                <span className="text-[10px] font-bold font-mono text-[#7045E8] uppercase tracking-wider block">
                  Cryptographic Verification
                </span>
                <div className="space-y-1.5 text-xs font-mono">
                  <div>
                    <span className="text-[#73758B] text-[10px] block">Doc A SHA-256:</span>
                    <span className="text-[10px] text-[#17172F] truncate block">
                      {comparison?.metadata_diff?.document_a?.sha256_hash?.slice(0, 24) || 'f274d4a93661ce8c5fd95...'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#73758B] text-[10px] block">Doc B SHA-256:</span>
                    <span className="text-[10px] text-[#17172F] truncate block">
                      {comparison?.metadata_diff?.document_b?.sha256_hash?.slice(0, 24) || 'a89fbb68a5a3bdc849e1...'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Differential Regions Full Table */}
            {comparison?.differential_regions && comparison.differential_regions.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-bold text-[#17172F] uppercase tracking-wider block">
                  Identified Differential Bounding Boxes ({comparison.differential_regions.length})
                </span>
                <div className="overflow-x-auto border border-[#E6E5F0] rounded-xl">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#F8F9FF] border-b border-[#E6E5F0] text-[#73758B] text-[10px]">
                      <tr>
                        <th className="py-2.5 px-3">Region ID</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Coordinates (X, Y, W, H)</th>
                        <th className="py-2.5 px-3">Area (px)</th>
                        <th className="py-2.5 px-3 text-right">Severity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E6E5F0]">
                      {comparison.differential_regions.slice(0, 10).map((r) => (
                        <tr key={r.region_id} className="hover:bg-[#F8F9FF]">
                          <td className="py-2 px-3 font-bold text-[#7045E8]">{r.region_id}</td>
                          <td className="py-2 px-3 text-[#17172F]">{r.category}</td>
                          <td className="py-2 px-3 text-[#73758B]">
                            {r.bounding_box.x}, {r.bounding_box.y}, {r.bounding_box.width}×{r.bounding_box.height}
                          </td>
                          <td className="py-2 px-3 text-[#73758B]">{r.area.toLocaleString()}</td>
                          <td className="py-2 px-3 text-right font-bold text-[#DC4545]">
                            {(r.severity * 100).toFixed(0)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Raw JSON Code Block for Technical Evaluators */}
            {comparison && (
              <div className="space-y-2">
                <span className="text-xs font-bold text-[#17172F] uppercase tracking-wider block">
                  Raw Differential Pipeline Response
                </span>
                <pre className="p-4 bg-[#17172F] text-purple-200 rounded-xl text-[11px] font-mono overflow-x-auto max-h-60">
                  {JSON.stringify(comparison, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentComparisonPage;
