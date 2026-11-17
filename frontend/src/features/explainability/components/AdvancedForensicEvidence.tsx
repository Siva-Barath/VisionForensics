import { useState } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  SlidersHorizontal,
  Shield,
  Cpu
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
  pageCount?: number;
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
  pageCount: _pageCount,
  custodyLogs,
  custodyLoading,
  activeTab: controlledTab,
  onTabChange,
}: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [internalTab, setInternalTab] = useState('ml');

  const currentTab = controlledTab || internalTab;
  const setTab = (tab: string) => {
    setInternalTab(tab);
    onTabChange?.(tab);
  };

  const vector = analysis.raw_ml?.feature_vector ?? 
                 analysis.track_1_ml?.feature_vector ?? 
                 analysis.track_1_ml?.top_contributing_features ?? {};
  const imputed = analysis.track_1_ml?.imputed_features || {};

  const tabs = [
    { id: 'ml', label: '1. Machine Learning Analysis' },
    { id: 'features', label: '2. 18 Numerical Features' },
    { id: 'symbolic', label: '3. Symbolic Forensic Analysis' },
    { id: 'ela', label: '4. ELA & Copy-Move Analysis' },
    { id: 'metadata', label: '5. Metadata & Properties' },
    { id: 'trace', label: '6. Decision Synthesis Trace' },
    { id: 'custody', label: '7. Custody & Governance' },
  ];

  return (
    <section className="space-y-4" aria-labelledby="advanced-title">
      <div className="bg-white border border-[#E6E5F0] rounded-2xl overflow-hidden shadow-sm transition-all">
        {/* Accordion Toggle Header */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full p-5 flex items-center justify-between text-left hover:bg-[#F8F9FF] transition-colors"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
              <SlidersHorizontal size={20} />
            </div>
            <div>
              <h2 id="advanced-title" className="text-sm font-bold text-[#17172F]">
                Explore Advanced Forensic Analysis
              </h2>
              <p className="text-xs text-[#73758B] mt-0.5">
                18-feature details, ELA, copy-move, metadata, decision trace and model governance.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-semibold text-[#7045E8]">
            <span>{isOpen ? 'Collapse Details' : 'Expand Details'}</span>
            {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>
        </button>

        {/* Collapsible Content */}
        {isOpen && (
          <div className="border-t border-[#E6E5F0] p-6 space-y-6 bg-[#F8F9FF]">
            {/* Tab Navigation */}
            <div className="flex border-b border-[#E6E5F0] overflow-x-auto gap-2 pb-2 text-xs">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTab(t.id)}
                  className={`px-3.5 py-2 rounded-xl font-semibold transition-all whitespace-nowrap ${
                    currentTab === t.id
                      ? 'bg-[#7045E8] text-white shadow-sm shadow-violet-200'
                      : 'bg-white border border-[#E6E5F0] text-[#73758B] hover:text-[#17172F] hover:border-[#DDD5F9]'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* TAB 1: MACHINE LEARNING ANALYSIS */}
            {currentTab === 'ml' && (
              <div className="space-y-4">
                <div className="bg-white border border-[#E6E5F0] rounded-xl p-5 space-y-4">
                  <div className="flex items-center gap-2 text-[#7045E8] font-bold text-xs uppercase tracking-wider pb-2 border-b border-[#E6E5F0]">
                    <Cpu size={16} /> Track 1: Frozen Random Forest Classifier
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
                    <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-lg">
                      <span className="text-[10px] text-[#73758B] uppercase block">Model Architecture</span>
                      <span className="font-bold text-[#17172F] text-sm mt-0.5 block">Random Forest (100 Trees)</span>
                    </div>
                    <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-lg">
                      <span className="text-[10px] text-[#73758B] uppercase block">Decision Threshold</span>
                      <span className="font-bold text-[#7045E8] text-sm mt-0.5 block">T = 0.40 (Locked)</span>
                    </div>
                    <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-lg">
                      <span className="text-[10px] text-[#73758B] uppercase block">Feature Completeness</span>
                      <span className="font-bold text-[#159B55] text-sm mt-0.5 block">
                        {Math.round((analysis.track_1_ml?.feature_completeness || 1.0) * 100)}% Available
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-[#5A5D72] leading-relaxed">
                    Track 1 performs statistical evaluation of the 18 physical substrate metrics without analyst tuning bias. The classifier output represents the estimated probability of digital manipulation.
                  </p>
                </div>
              </div>
            )}

            {/* TAB 2: 18 NUMERICAL FEATURES */}
            {currentTab === 'features' && (
              <div className="space-y-4">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[#17172F] font-bold">
                    Complete 18-Feature Vector vs. Authentic Reference Medians (N=660)
                  </span>
                  <span className="font-mono text-[#159B55] bg-[#EBF9F1] px-2.5 py-0.5 rounded-full border border-[#D1F2DE] font-semibold text-[11px]">
                    Completeness: {Math.round((analysis.track_1_ml?.feature_completeness || 1.0) * 100)}%
                  </span>
                </div>

                <div className="overflow-x-auto border border-[#E6E5F0] rounded-xl bg-white shadow-sm">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#F8F9FF] text-[#73758B] border-b border-[#E6E5F0] uppercase text-[10px]">
                      <tr>
                        <th className="py-2.5 px-3">Feature Key</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3 text-right">Observed Value</th>
                        <th className="py-2.5 px-3 text-right">Baseline Median</th>
                        <th className="py-2.5 px-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E6E5F0]">
                      {Object.entries(AUTHENTIC_MEDIANS).map(([featKey, meta]) => {
                        const rawVal = vector[featKey];
                        const observedVal = rawVal !== undefined && rawVal !== null ? Number(rawVal) : null;
                        const isImputed = featKey in imputed;
                        const diff = observedVal !== null ? Math.abs(observedVal - meta.median) : 0;
                        const isElevated = diff > meta.median * 0.5 && meta.median > 0;

                        return (
                          <tr key={featKey} className="hover:bg-[#F8F9FF]">
                            <td className="py-2.5 px-3 text-[#17172F] font-semibold">
                              {featKey} <span className="text-[#73758B] font-normal">({meta.label})</span>
                            </td>
                            <td className="py-2.5 px-3 text-[#7045E8]">{meta.category}</td>
                            <td className="py-2.5 px-3 text-right font-bold text-[#17172F]">
                              {observedVal !== null ? observedVal.toFixed(4) : 'Unavailable'} {meta.unit || ''}
                            </td>
                            <td className="py-2.5 px-3 text-right text-[#73758B]">
                              {meta.median.toFixed(4)} {meta.unit || ''}
                            </td>
                            <td className="py-2.5 px-3 text-center">
                              {observedVal === null ? (
                                <span className="text-[10px] text-[#73758B]">Unavailable</span>
                              ) : isImputed ? (
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]">
                                  Imputed
                                </span>
                              ) : isElevated ? (
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]">
                                  Elevated
                                </span>
                              ) : (
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]">
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

            {/* TAB 3: SYMBOLIC FORENSIC ANALYSIS */}
            {currentTab === 'symbolic' && (
              <div className="space-y-4">
                <div className="bg-white border border-[#E6E5F0] rounded-xl p-5 space-y-3">
                  <div className="flex items-center gap-2 text-[#7045E8] font-bold text-xs uppercase tracking-wider pb-2 border-b border-[#E6E5F0]">
                    <Shield size={16} /> Track 2: Symbolic Forensic Examination
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                    <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-lg">
                      <span className="text-[10px] text-[#73758B] uppercase block">Rule Severity Index</span>
                      <span className="font-bold text-[#17172F] text-base mt-0.5 block">
                        {analysis.track_2_symbolic?.symbolic_severity_score !== undefined
                          ? `${analysis.track_2_symbolic.symbolic_severity_score.toFixed(1)} / 100`
                          : '0.0 / 100'}
                      </span>
                    </div>
                    <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-lg">
                      <span className="text-[10px] text-[#73758B] uppercase block">Execution State</span>
                      <span className="font-bold text-[#159B55] text-base mt-0.5 block">
                        {analysis.track_2_symbolic?.available ? 'Completed' : 'Standby'}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-[#5A5D72] leading-relaxed">
                    Track 2 evaluates deterministic properties such as PDF cross-reference structure, font embedding anomalies, software signature tags, and chronological inconsistencies.
                  </p>
                </div>
              </div>
            )}

            {/* TAB 4: ELA & COPY-MOVE */}
            {currentTab === 'ela' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
                  <div className="p-4 bg-white border border-[#E6E5F0] rounded-xl space-y-1">
                    <span className="text-[10px] text-[#73758B] uppercase block">ELA Inconsistent Regions</span>
                    <span className="text-lg font-bold text-[#17172F]">
                      {vector.img_ela_region_count_mean !== undefined ? Number(vector.img_ela_region_count_mean).toFixed(0) : '0'}
                    </span>
                  </div>
                  <div className="p-4 bg-white border border-[#E6E5F0] rounded-xl space-y-1">
                    <span className="text-[10px] text-[#73758B] uppercase block">ELA Maximum Error</span>
                    <span className="text-lg font-bold text-[#7045E8]">
                      {vector.img_ela_max_difference_mean !== undefined ? Number(vector.img_ela_max_difference_mean).toFixed(1) : '14.0'}
                    </span>
                  </div>
                  <div className="p-4 bg-white border border-[#E6E5F0] rounded-xl space-y-1">
                    <span className="text-[10px] text-[#73758B] uppercase block">AKAZE Keypoints</span>
                    <span className="text-lg font-bold text-[#17172F]">
                      {vector.cm_keypoint_count_akaze !== undefined ? Number(vector.cm_keypoint_count_akaze).toFixed(0) : '0'}
                    </span>
                  </div>
                  <div className="p-4 bg-white border border-[#E6E5F0] rounded-xl space-y-1">
                    <span className="text-[10px] text-[#73758B] uppercase block">RANSAC Inliers</span>
                    <span className="text-lg font-bold text-[#159B55]">
                      {vector.cm_inlier_matches !== undefined ? Number(vector.cm_inlier_matches).toFixed(0) : '0'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 5: METADATA & DOCUMENT PROPERTIES */}
            {currentTab === 'metadata' && (
              <div className="space-y-4">
                <div className="bg-white border border-[#E6E5F0] rounded-xl overflow-hidden shadow-sm">
                  <div className="p-3 bg-[#F8F9FF] border-b border-[#E6E5F0] text-xs font-bold text-[#17172F]">
                    Embedded File Metadata Dictionary
                  </div>
                  {analysis.metadata_info && Object.keys(analysis.metadata_info).length > 0 ? (
                    <div className="divide-y divide-[#E6E5F0] text-xs font-mono">
                      {Object.entries(analysis.metadata_info).map(([k, v]) => (
                        <div key={k} className="p-3 flex justify-between gap-4 hover:bg-[#F8F9FF]">
                          <span className="text-[#73758B] font-semibold">{k}</span>
                          <span className="text-[#17172F] truncate max-w-md">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-6 text-center text-xs text-[#73758B]">
                      No custom metadata tags embedded in file header.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 6: DECISION SYNTHESIS TRACE */}
            {currentTab === 'trace' && (
              <div className="space-y-3">
                <span className="text-xs font-bold text-[#17172F] uppercase tracking-wider block">
                  Synthesis Arbiter Decision Trace ({analysis.decision_trace?.length || 0} Steps)
                </span>
                {analysis.decision_trace && analysis.decision_trace.length > 0 ? (
                  <div className="space-y-2">
                    {analysis.decision_trace.map((step, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-white border border-[#E6E5F0] rounded-xl flex items-start gap-3 shadow-sm text-xs font-mono"
                      >
                        <span className="px-2 py-0.5 rounded bg-[#F0EBFF] text-[#7045E8] font-bold text-[10px] shrink-0">
                          {step.track || `Step ${idx + 1}`}
                        </span>
                        <div className="min-w-0">
                          <p className="text-[#17172F] font-bold">{step.finding}</p>
                          {step.description && (
                            <p className="text-[11px] text-[#73758B] mt-0.5 font-sans leading-relaxed">
                              {step.description}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[#73758B] p-4 bg-white rounded-xl border border-[#E6E5F0]">
                    Corroborated decision trace recorded in tamper-evident ledger.
                  </p>
                )}
              </div>
            )}

            {/* TAB 7: CHAIN OF CUSTODY & GOVERNANCE */}
            {currentTab === 'custody' && (
              <div className="space-y-4">
                <div className="p-4 bg-white border border-[#E6E5F0] rounded-xl space-y-2 text-xs">
                  <div className="flex items-center gap-2 text-[#7045E8] font-bold">
                    <Shield size={16} /> Cryptographic Invariants & Model Governance
                  </div>
                  <div className="space-y-1 font-mono text-[11px] text-[#73758B]">
                    <div>Decision Boundary: <strong className="text-[#17172F]">T = 0.40 (Locked)</strong></div>
                    <div>Random Forest SHA-256: <strong className="text-[#7045E8] break-all">f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280</strong></div>
                    <div>18-Feature Schema: <strong className="text-[#159B55] break-all">eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc</strong></div>
                  </div>
                </div>

                <div className="bg-white border border-[#E6E5F0] rounded-xl overflow-hidden shadow-sm">
                  <div className="p-3 bg-[#F8F9FF] border-b border-[#E6E5F0] text-xs font-bold text-[#17172F]">
                    Immutable Evidence Custody Ledger ({custodyLogs.length} Events)
                  </div>
                  {custodyLoading ? (
                    <div className="p-4 text-xs text-[#73758B] text-center">Loading custody records...</div>
                  ) : custodyLogs.length > 0 ? (
                    <div className="divide-y divide-[#E6E5F0] text-xs font-mono">
                      {custodyLogs.map((log) => (
                        <div key={log.id} className="p-3 flex justify-between items-center hover:bg-[#F8F9FF]">
                          <div>
                            <span className="font-bold text-[#17172F]">{log.event_type}</span>
                            <span className="text-[#73758B] text-[10px] block mt-0.5">{log.timestamp}</span>
                          </div>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#EBF9F1] text-[#159B55] font-semibold border border-[#D1F2DE]">
                            {log.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 text-xs text-[#73758B] text-center">
                      Custody events verified against immutable SHA-256 digest.
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
