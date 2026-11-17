import { useState, useEffect, useMemo } from 'react';
import { 
  Layers, 
  ShieldAlert, 
  CheckCircle, 
  Loader2, 
  RefreshCw, 
  AlertTriangle,
  Cpu,
  Scale,
  Award,
  Binary,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import ServiceHealthPanel from '@/components/ServiceHealthPanel';
import { listDocuments, getWorkspaceStats, checkHealth } from '@/services/api';
import type { DocumentSummary, WorkspaceStats, HealthResponse } from '@/types';

// Top Gini Feature Importances from backend/app/ml/artifacts/feature_importance.json
const FEATURE_IMPORTANCES = [
  { feature: 'img_ela_max_difference_mean', label: 'Error Level Analysis (ELA) Max Diff', importance: 0.382, category: 'Compression & ELA' },
  { feature: 'img_laplacian_variance_mean', label: 'Laplacian Edge Variance (Focus)', importance: 0.107, category: 'Image Quality' },
  { feature: 'img_ela_region_count_mean', label: 'ELA Suspicious Region Count', importance: 0.096, category: 'Compression & ELA' },
  { feature: 'img_blur_severity_mean', label: 'Blur Severity Measure', importance: 0.071, category: 'Image Quality' },
  { feature: 'img_entropy_score_mean', label: 'Shannon Information Entropy', importance: 0.068, category: 'Texture' },
  { feature: 'img_edge_density_mean', label: 'Canny Edge Pixel Density', importance: 0.062, category: 'Texture' },
  { feature: 'img_illumination_std_mean', label: 'Illumination Uniformity Deviation', importance: 0.051, category: 'Image Quality' },
  { feature: 'cm_keypoint_count_akaze', label: 'AKAZE Keypoint Density', importance: 0.045, category: 'Copy-Move' },
  { feature: 'cm_descriptor_matches', label: 'Descriptor Distance Matches', importance: 0.032, category: 'Copy-Move' },
  { feature: 'cm_inlier_ratio', label: 'RANSAC Geometric Inlier Ratio', importance: 0.028, category: 'Copy-Move' },
  { feature: 'cm_inlier_matches', label: 'Geometric Inlier Pairs', importance: 0.025, category: 'Copy-Move' },
  { feature: 'img_noise_sigma_mean', label: 'High-Frequency Noise Sigma', importance: 0.022, category: 'Texture' },
];

export default function AnalyticsPage() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [totals, setTotals] = useState<WorkspaceStats | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchStats = () => {
    setLoading(true);
    setError(false);
    Promise.all([listDocuments(100, 0), getWorkspaceStats(), checkHealth().catch(() => null)])
      .then(([data, counts, healthData]) => {
        setTotals(counts);
        setHealth(healthData);
        setDocuments(data || []);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const stats = useMemo(() => {
    const total = totals?.total_documents ?? documents.length ?? 0;
    const highRisk = totals?.high_risk ?? documents.filter(d => d.unified_risk_tier === 'HIGH_RISK').length;
    const suspicious = totals?.requires_review ?? documents.filter(d => d.unified_risk_tier === 'SUSPICIOUS').length;
    const lowRisk = totals?.low_risk ?? documents.filter(d => d.unified_risk_tier === 'LOW_RISK').length;
    const other = Math.max(0, total - highRisk - suspicious - lowRisk);

    const highPct = total > 0 ? Math.round((highRisk / total) * 100) : 0;
    const suspPct = total > 0 ? Math.round((suspicious / total) * 100) : 0;
    const lowPct = total > 0 ? Math.round((lowRisk / total) * 100) : 0;

    // File type distribution
    const formats: Record<string, number> = {};
    documents.forEach((d) => {
      const ext = (d.file_type || 'other').toUpperCase();
      formats[ext] = (formats[ext] || 0) + 1;
    });

    const formatList = Object.entries(formats)
      .map(([label, count]) => ({
        label,
        count,
        pct: documents.length > 0 ? Math.round((count / documents.length) * 100) : 0,
      }))
      .sort((a, b) => b.count - a.count);

    return {
      total,
      highRisk,
      suspicious,
      lowRisk,
      other,
      highPct,
      suspPct,
      lowPct,
      formatList,
    };
  }, [documents, totals]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 pb-2 border-b border-[#E6E5F0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7045E8] bg-[#F0EBFF] px-2.5 py-0.5 rounded-full border border-[#DDD5F9]">
              Statistical Intelligence & Model Validation
            </span>
            <span className="text-[11px] font-mono text-[#73758B]">Random Forest (100 Trees)</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#17172F]">Caseload & Scientific Analytics</h1>
          <p className="text-xs text-[#73758B] mt-0.5">
            Empirical validation metrics, forensic feature importance rankings, and operational caseload distributions.
          </p>
        </div>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="p-2.5 bg-white border border-[#E6E5F0] hover:border-[#DDD5F9] hover:bg-[#F8F9FF] rounded-xl text-xs text-[#17172F] font-semibold transition-colors flex items-center gap-2 shadow-sm"
          title="Refresh Caseload Analytics"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin text-[#7045E8]' : 'text-[#7045E8]'} />
          <span>Refresh Data</span>
        </button>
      </div>

      {error && (
        <div role="alert" className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-2xl text-xs text-[#DC4545]">
          Analytics could not be loaded. Check backend connectivity and refresh.
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Document Exhibits', value: stats.total, icon: Layers, color: 'text-[#7045E8]', bg: 'bg-[#F0EBFF]' },
          { label: 'High Risk (Tampering)', value: stats.highRisk, icon: ShieldAlert, color: 'text-[#DC4545]', bg: 'bg-[#FDF2F2]' },
          { label: 'Requires Review', value: stats.suspicious, icon: AlertTriangle, color: 'text-[#E9A12A]', bg: 'bg-[#FFF8EC]' },
          { label: 'Low Risk (Authentic)', value: stats.lowRisk, icon: CheckCircle, color: 'text-[#159B55]', bg: 'bg-[#EBF9F1]' },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[11px] font-bold text-[#73758B] uppercase tracking-wider mb-1">{stat.label}</p>
                  <p className="text-3xl font-extrabold font-mono text-[#17172F]">
                    {loading ? <Loader2 size={24} className="animate-spin text-[#7045E8]" /> : stat.value}
                  </p>
                </div>
                <div className={`p-2.5 rounded-xl ${stat.bg}`}>
                  <Icon size={20} className={stat.color} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Operational Caseload Distributions (Clean Bar Charts) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Horizontal Bar Chart */}
        <Card variant="evidence" title="Operational Risk Breakdown">
          <div className="p-6 space-y-6">
            <div>
              <div className="flex justify-between items-center text-xs mb-2">
                <span className="font-bold text-[#17172F]">Composite Risk Distribution</span>
                <span className="text-[#73758B] font-mono">{stats.total} Total Documents</span>
              </div>
              {/* Stacked Horizontal Bar */}
              <div className="h-5 bg-[#F0EBFF] rounded-xl overflow-hidden flex border border-[#DDD5F9] p-0.5 gap-0.5">
                {stats.lowPct > 0 && (
                  <div
                    className="bg-[#159B55] rounded-lg transition-all duration-500"
                    style={{ width: `${stats.lowPct}%` }}
                    title={`Low Risk: ${stats.lowRisk} (${stats.lowPct}%)`}
                  />
                )}
                {stats.suspPct > 0 && (
                  <div
                    className="bg-[#E9A12A] rounded-lg transition-all duration-500"
                    style={{ width: `${stats.suspPct}%` }}
                    title={`Requires Review: ${stats.suspicious} (${stats.suspPct}%)`}
                  />
                )}
                {stats.highPct > 0 && (
                  <div
                    className="bg-[#DC4545] rounded-lg transition-all duration-500"
                    style={{ width: `${stats.highPct}%` }}
                    title={`High Risk: ${stats.highRisk} (${stats.highPct}%)`}
                  />
                )}
              </div>
            </div>

            {/* Individual Breakdown Bars */}
            <div className="space-y-4 pt-1">
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-[#159B55] font-bold flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#159B55]" /> Low Risk (Authentic Baselines)
                  </span>
                  <span className="font-mono text-[#17172F] font-bold">{stats.lowRisk} ({stats.lowPct}%)</span>
                </div>
                <div className="h-2.5 bg-[#F4F5FB] rounded-full overflow-hidden border border-[#E6E5F0]">
                  <div className="h-full bg-[#159B55] rounded-full" style={{ width: `${stats.lowPct}%` }} />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-[#E9A12A] font-bold flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#E9A12A]" /> Requires Review (Conflicting Signals)
                  </span>
                  <span className="font-mono text-[#17172F] font-bold">{stats.suspicious} ({stats.suspPct}%)</span>
                </div>
                <div className="h-2.5 bg-[#F4F5FB] rounded-full overflow-hidden border border-[#E6E5F0]">
                  <div className="h-full bg-[#E9A12A] rounded-full" style={{ width: `${stats.suspPct}%` }} />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-[#DC4545] font-bold flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#DC4545]" /> High Risk (Tampering Detected)
                  </span>
                  <span className="font-mono text-[#17172F] font-bold">{stats.highRisk} ({stats.highPct}%)</span>
                </div>
                <div className="h-2.5 bg-[#F4F5FB] rounded-full overflow-hidden border border-[#E6E5F0]">
                  <div className="h-full bg-[#DC4545] rounded-full" style={{ width: `${stats.highPct}%` }} />
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Document Format Breakdown Horizontal Bar Chart */}
        <Card variant="evidence" title="Exhibit File Format Breakdown">
          <div className="p-6 space-y-4">
            <p className="text-xs text-[#73758B]">
              Distribution of uploaded document MIME containers across recent case exhibits.
            </p>
            {stats.formatList.length === 0 ? (
              <p className="text-xs text-[#73758B] text-center py-8">No document exhibits recorded yet.</p>
            ) : (
              stats.formatList.map((item) => (
                <div key={item.label} className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-[#17172F] flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md bg-[#F0EBFF] text-[10px] font-mono text-[#7045E8] font-bold">
                        {item.label}
                      </span>
                      <span>{item.label === 'PDF' ? 'Portable Document Format' : `${item.label} Raster Image`}</span>
                    </span>
                    <span className="font-mono text-[#73758B]">
                      {item.count} exhibits ({item.pct}%)
                    </span>
                  </div>
                  <div className="h-2.5 bg-[#F4F5FB] rounded-full overflow-hidden border border-[#E6E5F0]">
                    <div
                      className="h-full bg-[#7045E8] rounded-full transition-all duration-500"
                      style={{ width: `${item.pct}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Machine Learning Model Validation Performance */}
      <Card variant="evidence" title="Machine Learning Validation Performance">
        <div className="p-6 space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 border-b border-[#E6E5F0]">
            <div>
              <div className="flex items-center gap-2">
                <Cpu size={16} className="text-[#7045E8]" />
                <span className="text-sm font-bold text-[#17172F]">Frozen Random Forest Architecture</span>
              </div>
              <p className="text-xs text-[#73758B] mt-0.5">
                Selected model artifact: <code className="text-[#7045E8] font-mono">random_forest.joblib</code> • 100 Trees • Operational Boundary <code className="text-[#7045E8] font-mono">T=0.40</code>
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-[#EBF9F1] border border-[#D1F2DE] rounded-full text-[#159B55] text-xs font-mono font-bold flex items-center gap-1.5">
                <Award size={14} /> ROC-AUC 0.9573
              </span>
            </div>
          </div>

          {/* Model Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 bg-[#F8F9FF] rounded-xl border border-[#E6E5F0] text-center">
              <div className="text-[10px] uppercase font-bold text-[#73758B] tracking-wider">Validation Accuracy</div>
              <div className="text-2xl font-extrabold font-mono text-[#17172F] mt-1">88.93%</div>
              <div className="text-[10px] text-[#73758B] mt-0.5">Overall Classification</div>
            </div>

            <div className="p-4 bg-[#F8F9FF] rounded-xl border border-[#E6E5F0] text-center">
              <div className="text-[10px] uppercase font-bold text-[#73758B] tracking-wider">ROC-AUC Score</div>
              <div className="text-2xl font-extrabold font-mono text-[#7045E8] mt-1">0.9573</div>
              <div className="text-[10px] text-[#73758B] mt-0.5">Discrimination Power</div>
            </div>

            <div className="p-4 bg-[#F8F9FF] rounded-xl border border-[#E6E5F0] text-center">
              <div className="text-[10px] uppercase font-bold text-[#73758B] tracking-wider">Precision-Recall AUC</div>
              <div className="text-2xl font-extrabold font-mono text-[#7045E8] mt-1">0.9652</div>
              <div className="text-[10px] text-[#73758B] mt-0.5">Positive Class AUC</div>
            </div>

            <div className="p-4 bg-[#F8F9FF] rounded-xl border border-[#E6E5F0] text-center">
              <div className="text-[10px] uppercase font-bold text-[#73758B] tracking-wider">Brier Loss Score</div>
              <div className="text-2xl font-extrabold font-mono text-[#159B55] mt-1">0.0812</div>
              <div className="text-[10px] text-[#73758B] mt-0.5">Probability Calibration</div>
            </div>
          </div>

          {/* Confusion Matrix Table & Per-Class Details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
            {/* Confusion Matrix */}
            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#17172F] flex items-center gap-1.5">
                <Binary size={14} className="text-[#7045E8]" /> Validation Confusion Matrix (N=280)
              </span>
              <div className="bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl p-4">
                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="p-3.5 bg-white border border-[#D1F2DE] rounded-xl shadow-sm">
                    <div className="text-[10px] uppercase font-bold text-[#73758B]">True Negatives (TN)</div>
                    <div className="text-2xl font-extrabold font-mono text-[#159B55] mt-1">137</div>
                    <div className="text-[10px] text-[#73758B] mt-0.5">Authentic Correctly Identified</div>
                  </div>

                  <div className="p-3.5 bg-white border border-[#FAD8D8] rounded-xl shadow-sm">
                    <div className="text-[10px] uppercase font-bold text-[#73758B]">False Positives (FP)</div>
                    <div className="text-2xl font-extrabold font-mono text-[#DC4545] mt-1">3</div>
                    <div className="text-[10px] text-[#DC4545] mt-0.5 font-semibold">False Alarm Rate: 2.14%</div>
                  </div>

                  <div className="p-3.5 bg-white border border-[#FFE8BF] rounded-xl shadow-sm">
                    <div className="text-[10px] uppercase font-bold text-[#73758B]">False Negatives (FN)</div>
                    <div className="text-2xl font-extrabold font-mono text-[#E9A12A] mt-1">28</div>
                    <div className="text-[10px] text-[#E9A12A] mt-0.5 font-semibold">Forged Specimen Missed</div>
                  </div>

                  <div className="p-3.5 bg-white border border-[#DDD5F9] rounded-xl shadow-sm">
                    <div className="text-[10px] uppercase font-bold text-[#73758B]">True Positives (TP)</div>
                    <div className="text-2xl font-extrabold font-mono text-[#7045E8] mt-1">112</div>
                    <div className="text-[10px] text-[#73758B] mt-0.5">Forged Correctly Detected</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Per-Class Precision & Recall */}
            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#17172F] flex items-center gap-1.5">
                <Scale size={14} className="text-[#7045E8]" /> Class-Level Precision & Recall
              </span>
              <div className="bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl p-4 space-y-4">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-[#17172F] font-bold">Forged Class Precision (Confidence)</span>
                    <span className="font-mono text-[#7045E8] font-extrabold">97.39%</span>
                  </div>
                  <div className="h-2.5 bg-white rounded-full overflow-hidden border border-[#E6E5F0]">
                    <div className="h-full bg-[#7045E8] rounded-full" style={{ width: '97.39%' }} />
                  </div>
                  <p className="text-[10px] text-[#73758B]">When flagged as forged, 97.4% accurate (minimal false accusations).</p>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-[#17172F] font-bold">Authentic Class Recall (Specificity)</span>
                    <span className="font-mono text-[#159B55] font-extrabold">97.86%</span>
                  </div>
                  <div className="h-2.5 bg-white rounded-full overflow-hidden border border-[#E6E5F0]">
                    <div className="h-full bg-[#159B55] rounded-full" style={{ width: '97.86%' }} />
                  </div>
                  <p className="text-[10px] text-[#73758B]">97.9% of genuine documents pass without false tampering flags.</p>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-[#17172F] font-bold">Forged Class Recall (Sensitivity)</span>
                    <span className="font-mono text-[#E9A12A] font-extrabold">80.00%</span>
                  </div>
                  <div className="h-2.5 bg-white rounded-full overflow-hidden border border-[#E6E5F0]">
                    <div className="h-full bg-[#E9A12A] rounded-full" style={{ width: '80.00%' }} />
                  </div>
                  <p className="text-[10px] text-[#73758B]">80.0% of manipulated documents detected by ML alone at T=0.55 validation threshold.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Top Forensic Feature Importance */}
      <Card variant="evidence" title="Forensic Feature Importance Ranking (Gini Importance)">
        <div className="p-6 space-y-4">
          <p className="text-xs text-[#73758B]">
            Relative contribution of extracted physical features to the Random Forest model's split decisions, derived from training on authentic and manipulated document corpora.
          </p>

          <div className="space-y-3 pt-2">
            {FEATURE_IMPORTANCES.map((item, index) => {
              const pct = (item.importance * 100).toFixed(1);
              return (
                <div key={item.feature} className="space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-5 text-right font-mono text-[10px] text-[#73758B]">{index + 1}.</span>
                      <span className="font-bold text-[#17172F]">{item.label}</span>
                      <span className="text-[10px] text-[#73758B] font-mono hidden sm:inline">({item.category})</span>
                    </div>
                    <span className="font-mono text-[#7045E8] font-bold text-xs">{pct}%</span>
                  </div>
                  <div className="h-2 bg-[#F0EBFF] rounded-full overflow-hidden border border-[#DDD5F9]">
                    <div
                      className="h-full bg-[#7045E8] rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(2, item.importance * 100 * 2.5)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Active Analysis Engines */}
      <Card variant="evidence" title="Active Forensic Inspection Engines">
        <ServiceHealthPanel health={health} />
      </Card>
    </div>
  );
}
