import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  GitCompare,
  RefreshCw,
  AlertCircle,
  FileCheck2,
  Shield,
  Layers,
} from 'lucide-react';
import { compareDocuments, getDocumentImageUrl, getComparisonArtifactUrl, listDocuments } from '@/services/api';
import type { ComparisonResponse, DifferentialRegion, DocumentSummary } from '@/types';
import { ComparisonToolbar, ViewMode } from '../components/ComparisonToolbar';
import { SynchronizedDualViewer } from '../components/SynchronizedDualViewer';
import { DifferentialInspector } from '../components/DifferentialInspector';
import { ComparisonSummaryPanel } from '../components/ComparisonSummaryPanel';

export const DocumentComparisonPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [exhibits, setExhibits] = useState<DocumentSummary[]>([]);
  useEffect(() => { listDocuments(100, 0).then(setExhibits).catch(() => setExhibits([])); }, []);

  // Document IDs from query params
  const paramDocA = searchParams.get('docA') || '';
  const paramDocB = searchParams.get('docB') || '';

  const [docAId, setDocAId] = useState(paramDocA);
  const [docBId, setDocBId] = useState(paramDocB);
  const [pageA, setPageA] = useState(0);
  const [pageB, setPageB] = useState(0);
  const [alignImages] = useState(true);

  // Comparison State
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Viewer Controls
  const [viewMode, setViewMode] = useState<ViewMode>('side-by-side');
  const [scale, setScale] = useState(1);
  const [isSynchronized, setIsSynchronized] = useState(true);
  const [overlayOpacity, setOverlayOpacity] = useState(0.5);

  // Inspection Selection
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
        // Sync URL search params
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

  // Trigger comparison when query params are provided on mount
  useEffect(() => {
    if (paramDocA && paramDocB) {
      setDocAId(paramDocA);
      setDocBId(paramDocB);
      runComparison(paramDocA, paramDocB, pageA, pageB, alignImages);
    }
  }, [paramDocA, paramDocB]);

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

  const handlePageAChange = (newPage: number) => {
    setPageA(newPage);
    if (docAId && docBId) {
      runComparison(docAId, docBId, newPage, pageB, alignImages);
    }
  };

  const handlePageBChange = (newPage: number) => {
    setPageB(newPage);
    if (docAId && docBId) {
      runComparison(docAId, docBId, pageA, newPage, alignImages);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-ink-bg text-gray-200 overflow-hidden font-sans">
      {/* Top Workspace Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-ink-panel border-b border-ink-border shrink-0 z-20">
      <datalist id="comparison-exhibits">{exhibits.map(doc => <option key={doc.id} value={doc.id}>{doc.original_filename}</option>)}</datalist>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand/20 border border-brand text-brand">
            <GitCompare size={18} />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              DOCUMENT COMPARISON & DIFFERENTIAL WORKSPACE
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-brand/20 text-brand border border-brand/40">
                Milestone 7D
              </span>
            </h1>
            <p className="text-[11px] text-gray-400 font-mono">
              Geometric Registration • Structural SSIM • Differential Heatmaps
            </p>
          </div>
        </div>

        {/* Document Selection Inputs Bar */}
        <form onSubmit={handleStartComparison} className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-ink-bg border border-ink-border rounded-lg px-2.5 py-1 text-xs font-mono">
            <span className="text-blue-400 font-bold">Doc A:</span>
            <input
              type="text"
              list="comparison-exhibits" aria-label="First exhibit" placeholder="Select or enter exhibit ID"
              value={docAId}
              onChange={(e) => setDocAId(e.target.value)}
              className="bg-transparent text-white outline-none w-36 placeholder-gray-500"
            />
          </div>

          <div className="text-gray-500 font-mono text-xs">vs</div>

          <div className="flex items-center gap-1.5 bg-ink-bg border border-ink-border rounded-lg px-2.5 py-1 text-xs font-mono">
            <span className="text-amber-400 font-bold">Doc B:</span>
            <input
              type="text"
              list="comparison-exhibits" aria-label="Second exhibit" placeholder="Select or enter exhibit ID"
              value={docBId}
              onChange={(e) => setDocBId(e.target.value)}
              className="bg-transparent text-white outline-none w-36 placeholder-gray-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !docAId.trim() || !docBId.trim()}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-brand hover:bg-brand/90 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            {loading ? <RefreshCw size={13} className="animate-spin" /> : <GitCompare size={13} />}
            <span>Compare</span>
          </button>
        </form>
      </header>

      {/* Main Workspace Body */}
      {error && (
        <div className="mx-6 mt-3 p-3 bg-red-950/40 border border-red-800/80 rounded-lg flex items-center justify-between text-xs text-red-300">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="text-red-400 shrink-0" />
            <span className="font-mono">{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-gray-400 hover:text-white font-mono text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {!comparison && !loading ? (
        // Empty State: Prompt user to select documents
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-ink-bg overflow-y-auto">
          <div className="w-16 h-16 rounded-2xl bg-brand/10 border border-brand/30 flex items-center justify-center text-brand mb-4">
            <GitCompare size={32} />
          </div>
          <h2 className="text-xl font-bold text-white mb-1">Dual-Document Forensic Comparison</h2>
          <p className="text-xs text-gray-400 max-w-lg mb-6 leading-relaxed">
            Select two document exhibits to perform automated geometric image registration, calculate structural similarity (SSIM), generate pixel-level difference heatmaps, and inspect localized modifications.
          </p>

          {/* Quick Exhibit Selection Card */}
          {exhibits.length > 0 && (
            <div className="w-full max-w-2xl bg-ink-panel border border-ink-border rounded-lg p-6 mb-8 text-left shadow-lg">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                <GitCompare size={15} className="text-brand" /> Select Exhibits to Compare
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-[11px] font-semibold text-blue-400 uppercase tracking-wider mb-1.5">
                    Exhibit A (Reference / Baseline)
                  </label>
                  <select
                    value={docAId}
                    onChange={(e) => setDocAId(e.target.value)}
                    className="w-full px-3 py-2 bg-ink-bg border border-ink-border rounded-md text-xs text-white focus:outline-none focus:border-brand font-sans"
                  >
                    <option value="">-- Choose First Exhibit --</option>
                    {exhibits.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.original_filename} ({d.file_type.toUpperCase()})
                      </option>
                    ))}
                  </select>
                  {docAId && (
                    <p className="text-[10px] text-gray-400 font-mono mt-1 truncate">ID: {docAId}</p>
                  )}
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-amber-400 uppercase tracking-wider mb-1.5">
                    Exhibit B (Questioned Document)
                  </label>
                  <select
                    value={docBId}
                    onChange={(e) => setDocBId(e.target.value)}
                    className="w-full px-3 py-2 bg-ink-bg border border-ink-border rounded-md text-xs text-white focus:outline-none focus:border-brand font-sans"
                  >
                    <option value="">-- Choose Second Exhibit --</option>
                    {exhibits.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.original_filename} ({d.file_type.toUpperCase()})
                      </option>
                    ))}
                  </select>
                  {docBId && (
                    <p className="text-[10px] text-gray-400 font-mono mt-1 truncate">ID: {docBId}</p>
                  )}
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  disabled={!docAId || !docBId || docAId === docBId}
                  onClick={() => runComparison(docAId, docBId, pageA, pageB, alignImages)}
                  className="px-6 py-2.5 bg-brand hover:bg-brand-hover disabled:opacity-40 text-white rounded-md text-xs font-bold transition-all flex items-center gap-2 shadow-sm"
                >
                  <GitCompare size={15} /> Run Differential Comparison
                </button>
              </div>
              {docAId && docBId && docAId === docBId && (
                <p className="text-[11px] text-amber-400 mt-2">
                  * Please select two different exhibits to perform differential comparison.
                </p>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl text-left">
            <div className="p-3 bg-ink-panel border border-ink-border rounded-lg">
              <div className="text-brand font-mono text-xs font-semibold mb-1 flex items-center gap-1.5">
                <Shield size={14} /> Defensible Isolation
              </div>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Original files and SHA-256 hashes are immutable. All comparison artifacts are isolated
                in dedicated storage.
              </p>
            </div>

            <div className="p-3 bg-ink-panel border border-ink-border rounded-lg">
              <div className="text-brand font-mono text-xs font-semibold mb-1 flex items-center gap-1.5">
                <Layers size={14} /> Geometric Registration
              </div>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                ORB feature alignment and RANSAC homography align exhibits with varying dimensions or
                scanner tilts.
              </p>
            </div>

            <div className="p-3 bg-ink-panel border border-ink-border rounded-lg">
              <div className="text-brand font-mono text-xs font-semibold mb-1 flex items-center gap-1.5">
                <FileCheck2 size={14} /> Multi-Page Support
              </div>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Compare multi-page PDFs page-by-page with independent or synchronized page navigation.
              </p>
            </div>
          </div>
        </div>
      ) : loading ? (
        // Loading State
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-ink-bg">
          <RefreshCw size={36} className="text-brand animate-spin mb-4" />
          <h2 className="text-sm font-bold text-white font-mono">Executing Differential Analysis...</h2>
          <p className="text-xs text-gray-400 font-mono mt-1">
            Extracting pages • Computing ORB descriptors • Calculating SSIM • Generating Diff Heatmap
          </p>
        </div>
      ) : comparison ? (
        // Active Comparison Workspace
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Comparison Toolbar */}
          <ComparisonToolbar
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            scale={scale}
            onZoomIn={() => setScale((s) => Math.min(Math.round((s + 0.25) * 100) / 100, 3.5))}
            onZoomOut={() => setScale((s) => Math.max(Math.round((s - 0.25) * 100) / 100, 0.25))}
            onResetZoom={() => setScale(1)}
            isSynchronized={isSynchronized}
            onToggleSync={() => setIsSynchronized(!isSynchronized)}
            alignment={comparison.alignment}
            onSwapDocuments={handleSwapDocuments}
            overlayOpacity={overlayOpacity}
            onOverlayOpacityChange={setOverlayOpacity}
          />

          {/* Center Canvas & Sidebar */}
          <div className="flex-1 flex overflow-hidden">
            {/* Dual Synchronized Canvas */}
            <SynchronizedDualViewer
              docAUrl={getDocumentImageUrl(comparison.document_a_id, comparison.page_a)}
              docBUrl={getDocumentImageUrl(comparison.document_b_id, comparison.page_b)}
              alignedBUrl={getComparisonArtifactUrl(comparison.comparison_id, 'aligned_b')}
              diffHeatmapUrl={getComparisonArtifactUrl(comparison.comparison_id, 'diff_heatmap')}
              diffMaskUrl={getComparisonArtifactUrl(comparison.comparison_id, 'diff_mask')}
              regions={comparison.differential_regions}
              selectedRegionId={selectedRegion ? selectedRegion.region_id : null}
              hoveredRegionId={hoveredRegionId}
              onRegionSelect={setSelectedRegion}
              onRegionHover={setHoveredRegionId}
              viewMode={viewMode}
              scale={scale}
              isSynchronized={isSynchronized}
              overlayOpacity={overlayOpacity}
              docADims={comparison.metadata_diff.document_a.dimensions}
              docBDims={comparison.metadata_diff.document_b.dimensions}
              docAName={comparison.metadata_diff.document_a.filename}
              docBName={comparison.metadata_diff.document_b.filename}
              pageA={comparison.page_a}
              pageB={comparison.page_b}
              pageCountA={comparison.metadata_diff.document_a.page_count}
              pageCountB={comparison.metadata_diff.document_b.page_count}
              onPageAChange={handlePageAChange}
              onPageBChange={handlePageBChange}
            />

            {/* Differential Regions Inspector */}
            <div className="w-80 shrink-0 h-full">
              <DifferentialInspector
                regions={comparison.differential_regions}
                selectedRegionId={selectedRegion ? selectedRegion.region_id : null}
                onRegionSelect={setSelectedRegion}
                onRegionHover={setHoveredRegionId}
              />
            </div>
          </div>

          {/* Bottom Summary Panel */}
          <ComparisonSummaryPanel
            metrics={comparison.metrics}
            metadataDiff={comparison.metadata_diff}
            summary={comparison.summary}
          />
        </div>
      ) : null}
    </div>
  );
};

export default DocumentComparisonPage;
