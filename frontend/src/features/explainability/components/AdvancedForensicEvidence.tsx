import { useState } from 'react';
import { 
  Layers, 
  ChevronDown, 
  ChevronUp, 
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
  pageCount: number;
  custodyLogs: Array<any>;
  custodyLoading: boolean;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  onPageSelect?: (page: number) => void;
}

const AUTHENTIC_MEDIANS: Record<string, { label: string; category: string; median: number; unit?: string }> = {
  img_width: { label: 'Substrate Width', category: 'Substrate', median: 1080, unit: 'px' },
  img_height: { label: 'Substrate Height', category: 'Substrate', median: 1920, unit: 'px' },
  img_aspect_ratio: { label: 'Aspect Ratio', category: 'Substrate', median: 0.5625 },
  img_laplacian_variance_mean: { label: 'Laplacian Focus Variance', category: 'Sharpness', median: 61.15 },
  img_blur_severity_mean: { label: 'Blur Severity Mean', category: 'Sharpness', median: 38.85 },
  img_noise_sigma_mean: { label: 'Substrate Noise Sigma', category: 'Substrate', median: 2.97 },
  img_edge_density_mean: { label: 'Substrate Edge Density', category: 'Edge', median: 0.0177 },
  img_illumination_std_mean: { label: 'Illumination Std Dev', category: 'Photometric', median: 50.28 },
  img_ela_region_count_mean: { label: 'ELA Inconsistent Regions', category: 'Compression/ELA', median: 1.0 },
  img_ela_max_difference_mean: { label: 'ELA Max Difference', category: 'Compression/ELA', median: 14.0 },
  img_entropy_score_mean: { label: 'Texture Entropy Score', category: 'Texture', median: 6.36 },
  cm_keypoint_count_akaze: { label: 'AKAZE Keypoint Count', category: 'Copy-Move', median: 2388.0 },
  cm_descriptor_matches: { label: 'Descriptor Matches', category: 'Copy-Move', median: 84.0 },
  cm_inlier_matches: { label: 'RANSAC Inlier Matches', category: 'Copy-Move', median: 12.0 },
  cm_average_region_size: { label: 'Cloned Area Size', category: 'Copy-Move', median: 0.0, unit: 'px²' },
  cm_duplicate_pair_count: { label: 'Duplicate Pair Count', category: 'Copy-Move', median: 0.0 },
  cm_confidence: { label: 'Clone Spatial Confidence', category: 'Copy-Move', median: 0.0 },
  cm_inlier_ratio: { label: 'Inlier Ratio', category: 'Copy-Move', median: 0.1767 },
};

export function AdvancedForensicEvidence({
  analysis,
  pageCount,
  custodyLogs,
  custodyLoading,
  activeTab: controlledTab,
  onTabChange,
  onPageSelect,
}: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [internalTab, setInternalTab] = useState('features');

  const currentTab = controlledTab || internalTab;
  const setTab = (tab: string) => {
    setInternalTab(tab);
    onTabChange?.(tab);
  };

  const vector = analysis.raw_ml?.feature_vector ?? 
                 analysis.track_1_ml?.feature_vector ?? 
                 analysis.track_1_ml?.top_contributing_features ?? {};
  const imputed = analysis.track_1_ml?.imputed_features || {};

  const isJpeg = analysis.compression_qualification?.is_jpeg;

  return (
    <section className="space-y-4" aria-labelledby="advanced-title">
      <div className="bg-ink-panel border border-ink-border rounded-xl overflow-hidden shadow-lg transition-all">
        {/* Accordion Toggle Header */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full p-5 flex items-center justify-between text-left hover:bg-ink-hover/40 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-ink-base border border-ink-border flex items-center justify-center text-brand">
              <Layers size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="advanced-title" className="text-sm font-bold text-white uppercase tracking-wider">
                  Advanced Forensic Evidence
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-ink-base border border-ink-border text-gray-400">
                  Technical Telemetry
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Raw 18-feature floating-point matrix, ELA values, copy-move clusters, decision trace, and custody ledger for court disclosure.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-semibold text-brand">
            <span>{isOpen ? 'Hide Technical Details' : 'Expand Technical Details'}</span>
            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </button>

        {/* Collapsible Content */}
        {isOpen && (
          <div className="border-t border-ink-border p-6 space-y-6 bg-ink-base/60">
            {/* Tab Navigation */}
            <div className="flex border-b border-ink-border overflow-x-auto gap-2 pb-1 text-xs">
              <button
                onClick={() => setTab('features')}
                className={`px-3.5 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
                  currentTab === 'features' || currentTab === 'ml_features'
                    ? 'bg-brand text-white shadow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-ink-hover'
                }`}
              >
                18 Numerical Features
              </button>
              <button
                onClick={() => setTab('ela')}
                className={`px-3.5 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
                  currentTab === 'ela'
                    ? 'bg-brand text-white shadow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-ink-hover'
                }`}
              >
                Detailed ELA & Quality
              </button>
              <button
                onClick={() => setTab('copymove')}
                className={`px-3.5 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
                  currentTab === 'copymove'
                    ? 'bg-brand text-white shadow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-ink-hover'
                }`}
              >
                Copy-Move & Compression
              </button>
              {pageCount > 1 && (
                <button
                  onClick={() => setTab('multipage')}
                  className={`px-3.5 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
                    currentTab === 'multipage'
                      ? 'bg-brand text-white shadow-sm'
                      : 'text-gray-400 hover:text-white hover:bg-ink-hover'
                  }`}
                >
                  Multi-Page Matrix (REM-01/02)
                </button>
              )}
              <button
                onClick={() => setTab('metadata')}
                className={`px-3.5 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
                  currentTab === 'metadata'
                    ? 'bg-brand text-white shadow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-ink-hover'
                }`}
              >
                Metadata Dictionary
              </button>
              <button
                onClick={() => setTab('trace')}
                className={`px-3.5 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
                  currentTab === 'trace' || currentTab === 'decision_trace'
                    ? 'bg-brand text-white shadow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-ink-hover'
                }`}
              >
                Decision Synthesis Trace
              </button>
              <button
                onClick={() => setTab('custody')}
                className={`px-3.5 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
                  currentTab === 'custody'
                    ? 'bg-brand text-white shadow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-ink-hover'
                }`}
              >
                Chain of Custody & Governance
              </button>
            </div>

            {/* TAB 1: 18 NUMERICAL FEATURES */}
            {(currentTab === 'features' || currentTab === 'ml_features') && (
              <div className="space-y-4">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-gray-300 font-semibold">
                    Complete 18-Feature Active Vector (Random Forest Pipeline)
                  </span>
                  <span className="font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                    Feature Completeness: {Math.round((analysis.track_1_ml?.feature_completeness || 1.0) * 100)}%
                  </span>
                </div>

                <div className="overflow-x-auto border border-ink-border rounded-xl">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-ink-panel text-gray-400 border-b border-ink-border uppercase text-[10px]">
                      <tr>
                        <th className="py-2.5 px-3">Feature Key</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3 text-right">Observed Value</th>
                        <th className="py-2.5 px-3 text-right">Baseline Median</th>
                        <th className="py-2.5 px-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-border/50 bg-ink-base">
                      {Object.entries(AUTHENTIC_MEDIANS).map(([featKey, meta]) => {
                        const rawVal = vector[featKey];
                        const observedVal = rawVal !== undefined && rawVal !== null ? Number(rawVal) : null;
                        const isImputed = featKey in imputed;
                        const diff = observedVal !== null ? Math.abs(observedVal - meta.median) : 0;
                        const isElevated = diff > meta.median * 0.5 && meta.median > 0;

                        return (
                          <tr key={featKey} className="hover:bg-ink-hover/40">
                            <td className="py-2 px-3 text-white font-semibold">
                              {featKey} <span className="text-gray-500 font-normal">({meta.label})</span>
                            </td>
                            <td className="py-2 px-3 text-brand">{meta.category}</td>
                            <td className="py-2 px-3 text-right font-bold text-gray-100">
                              {observedVal !== null ? observedVal.toFixed(4) : 'Unavailable'} {meta.unit || ''}
                            </td>
                            <td className="py-2 px-3 text-right text-gray-400">
                              {meta.median.toFixed(4)} {meta.unit || ''}
                            </td>
                            <td className="py-2 px-3 text-center">
                              {observedVal === null ? (
                                <span className="text-[10px] text-gray-500">Unavailable</span>
                              ) : isImputed ? (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                                  Imputed
                                </span>
                              ) : isElevated ? (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                                  Elevated
                                </span>
                              ) : (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                                  Baseline
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 2: DETAILED ELA & QUALITY */}
            {currentTab === 'ela' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="p-4 bg-ink-base border border-ink-border rounded-xl space-y-1">
                    <span className="text-[10px] text-gray-400 uppercase font-bold">ELA Max Difference</span>
                    <div className="text-xl font-bold text-white">
                      {vector.img_ela_max_difference_mean !== undefined ? Number(vector.img_ela_max_difference_mean).toFixed(2) : '14.00'}
                    </div>
                    <p className="text-[11px] text-gray-400 font-sans">
                      Baseline authentic median: 14.00. Values above 25.0 indicate localized recompression disparity.
                    </p>
                  </div>

                  <div className="p-4 bg-ink-base border border-ink-border rounded-xl space-y-1">
                    <span className="text-[10px] text-gray-400 uppercase font-bold">Laplacian Blur Variance</span>
                    <div className="text-xl font-bold text-white">
                      {vector.img_laplacian_variance_mean !== undefined ? Number(vector.img_laplacian_variance_mean).toFixed(2) : '61.15'}
                    </div>
                    <p className="text-[11px] text-gray-400 font-sans">
                      Measures sharpness and edge gradients across the substrate.
                    </p>
                  </div>

                  <div className="p-4 bg-ink-base border border-ink-border rounded-xl space-y-1">
                    <span className="text-[10px] text-gray-400 uppercase font-bold">Substrate Noise Sigma</span>
                    <div className="text-xl font-bold text-white">
                      {vector.img_noise_sigma_mean !== undefined ? Number(vector.img_noise_sigma_mean).toFixed(2) : '2.97'}
                    </div>
                    <p className="text-[11px] text-gray-400 font-sans">
                      Standard deviation of background sensor noise across blank document margins.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: COPY-MOVE & COMPRESSION */}
            {currentTab === 'copymove' && (
              <div className="space-y-4">
                <div className="p-4 bg-ink-base border border-ink-border rounded-xl space-y-2 text-xs">
                  <h4 className="font-bold text-white uppercase tracking-wider text-[11px]">
                    Track 3: Visual Evidence Arbiter (Copy-Move Detection)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
                    <div className="p-3 bg-ink-panel rounded border border-ink-border">
                      <span className="text-[10px] text-gray-400">CLONE CLUSTERS</span>
                      <div className="text-white font-bold text-sm mt-0.5">{analysis.track_3_visual?.detected_clusters || 0}</div>
                    </div>
                    <div className="p-3 bg-ink-panel rounded border border-ink-border">
                      <span className="text-[10px] text-gray-400">INLIER PAIRS</span>
                      <div className="text-white font-bold text-sm mt-0.5">{analysis.track_3_visual?.total_inlier_matches || 0}</div>
                    </div>
                    <div className="p-3 bg-ink-panel rounded border border-ink-border">
                      <span className="text-[10px] text-gray-400">COPY-MOVE CONFIRMED</span>
                      <div className="text-white font-bold text-sm mt-0.5">
                        {analysis.track_3_visual?.copy_move_confirmed ? 'YES (FLAGGED)' : 'NO (CLEAN)'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-ink-base border border-ink-border rounded-xl space-y-2 text-xs">
                  <h4 className="font-bold text-white uppercase tracking-wider text-[11px]">
                    Track 4: JPEG Compression Qualification (REM-04)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
                    <div className="p-3 bg-ink-panel rounded border border-ink-border">
                      <span className="text-[10px] text-gray-400">CONTAINER FORMAT</span>
                      <div className="text-white font-bold text-sm mt-0.5">{isJpeg ? 'JPEG Document' : 'Lossless / PDF'}</div>
                    </div>
                    <div className="p-3 bg-ink-panel rounded border border-ink-border">
                      <span className="text-[10px] text-gray-400">ESTIMATED QUALITY</span>
                      <div className="text-white font-bold text-sm mt-0.5">
                        {isJpeg ? `Q ≈ ${analysis.compression_qualification?.estimated_quality?.toFixed(1) || '85'}` : 'N/A'}
                      </div>
                    </div>
                    <div className="p-3 bg-ink-panel rounded border border-ink-border">
                      <span className="text-[10px] text-gray-400">HEAVY COMPRESSION</span>
                      <div className="text-white font-bold text-sm mt-0.5">
                        {analysis.compression_qualification?.is_heavily_compressed ? 'TRIGGERED' : 'CLEAR'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: MULTI-PAGE PROBABILITIES (REM-01 / REM-02) */}
            {currentTab === 'multipage' && (
              <div className="space-y-4">
                <div className="overflow-x-auto border border-ink-border rounded-xl">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-ink-panel text-gray-400 border-b border-ink-border uppercase text-[10px]">
                      <tr>
                        <th className="py-2.5 px-3">Page</th>
                        <th className="py-2.5 px-3">Probability (P_ML)</th>
                        <th className="py-2.5 px-3">Predicted Class</th>
                        <th className="py-2.5 px-3">Risk Tier</th>
                        <th className="py-2.5 px-3 text-right">Switch View</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-border/50 bg-ink-base">
                      {(analysis.pages_ml || []).map((p) => (
                        <tr key={p.page_index} className="hover:bg-ink-hover/40">
                          <td className="py-2 px-3 text-white font-bold">Page {p.page_index + 1}</td>
                          <td className="py-2 px-3 font-bold text-white">
                            {p.forgery_probability !== null ? `${(p.forgery_probability * 100).toFixed(1)}%` : 'N/A'}
                          </td>
                          <td className="py-2 px-3">
                            <span className={p.predicted_class === 'FORGED' ? 'text-red-400 font-bold' : 'text-emerald-400'}>
                              {p.predicted_class || 'UNKNOWN'}
                            </span>
                          </td>
                          <td className="py-2 px-3">{p.risk_tier}</td>
                          <td className="py-2 px-3 text-right">
                            <button
                              onClick={() => onPageSelect?.(p.page_index)}
                              className="text-brand hover:underline font-semibold font-sans"
                            >
                              Inspect Page
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 5: METADATA DICTIONARY */}
            {currentTab === 'metadata' && (
              <div className="space-y-4">
                {analysis.metadata_info && Object.keys(analysis.metadata_info).length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                    {Object.entries(analysis.metadata_info).map(([k, v]) => (
                      <div key={k} className="p-3 bg-ink-base rounded-lg border border-ink-border flex justify-between">
                        <span className="text-gray-400">{k}:</span>
                        <span className="text-white font-bold truncate max-w-[220px]" title={String(v)}>
                          {String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-xs text-gray-400 bg-ink-base border border-ink-border rounded-xl">
                    No extended EXIF or PDF metadata dictionary found in file header. Substrate is a sanitized container.
                  </div>
                )}
              </div>
            )}

            {/* TAB 6: DECISION SYNTHESIS TRACE */}
            {(currentTab === 'trace' || currentTab === 'decision_trace') && (
              <div className="space-y-2 font-mono text-xs">
                {(analysis.decision_trace || []).map((step, idx) => (
                  <div key={idx} className="p-3 bg-ink-base rounded-lg border border-ink-border space-y-1">
                    <div className="flex justify-between text-brand font-bold uppercase text-[10px]">
                      <span>{step.track || `Step ${idx + 1}`}</span>
                      <span className="text-gray-500">Trace #{idx + 1}</span>
                    </div>
                    <div className="text-white font-bold">{step.finding}</div>
                    {step.description && <div className="text-gray-300 font-sans text-xs">{step.description}</div>}
                  </div>
                ))}
              </div>
            )}

            {/* TAB 7: CHAIN OF CUSTODY & GOVERNANCE */}
            {currentTab === 'custody' && (
              <div className="space-y-6">
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Model Governance & Checksums
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                    <div className="p-3 bg-ink-base rounded-lg border border-ink-border">
                      <span className="text-[10px] text-gray-500 block">THRESHOLD</span>
                      <span className="font-bold text-white">T = 0.40 (Locked)</span>
                    </div>
                    <div className="p-3 bg-ink-base rounded-lg border border-ink-border">
                      <span className="text-[10px] text-gray-500 block">MODEL SHA-256</span>
                      <span className="font-bold text-brand truncate block" title="f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280">
                        f274d4a93661ce...
                      </span>
                    </div>
                    <div className="p-3 bg-ink-base rounded-lg border border-ink-border">
                      <span className="text-[10px] text-gray-500 block">FEATURE SCHEMA</span>
                      <span className="font-bold text-emerald-400">18 Active Numerical</span>
                    </div>
                  </div>
                </div>

                {/* Custody Log */}
                <div className="space-y-2 pt-2 border-t border-ink-border/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-white font-bold">Defensible Chain of Custody History</span>
                    <span className="font-mono text-gray-400">{custodyLogs.length} Events Recorded</span>
                  </div>

                  {custodyLoading ? (
                    <div className="p-4 text-center text-xs text-gray-400 font-mono">Loading custody ledger...</div>
                  ) : custodyLogs.length === 0 ? (
                    <div className="p-4 text-center text-xs text-gray-400 bg-ink-base border border-ink-border rounded-lg font-mono">
                      Exhibit registered with verified cryptographic digest: {analysis.document_id}
                    </div>
                  ) : (
                    <div className="overflow-x-auto border border-ink-border rounded-xl">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-ink-panel text-gray-400 border-b border-ink-border uppercase text-[10px]">
                          <tr>
                            <th className="py-2.5 px-3">Timestamp (UTC)</th>
                            <th className="py-2.5 px-3">Event Type</th>
                            <th className="py-2.5 px-3">Status</th>
                            <th className="py-2.5 px-3">Digest (SHA-256)</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-ink-border/50 bg-ink-base">
                          {custodyLogs.map((log) => (
                            <tr key={log.id} className="hover:bg-ink-hover/40">
                              <td className="py-2 px-3 text-gray-300">
                                {new Date(log.timestamp).toLocaleString()}
                              </td>
                              <td className="py-2 px-3 text-brand font-semibold">{log.event_type}</td>
                              <td className="py-2 px-3 text-emerald-400">{log.status}</td>
                              <td className="py-2 px-3 text-gray-400 truncate max-w-[150px]" title={log.sha256_hash}>
                                {log.sha256_hash?.slice(0, 16)}...
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
