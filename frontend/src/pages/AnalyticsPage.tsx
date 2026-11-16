import { useState, useEffect, useMemo } from 'react';
import { Layers, ShieldAlert, CheckCircle, Loader2, RefreshCw, AlertTriangle } from 'lucide-react';
import Card from '@/components/ui/Card';
import ServiceHealthPanel from '@/components/ServiceHealthPanel';
import { listDocuments, getWorkspaceStats, checkHealth } from '@/services/api';
import type { DocumentSummary, WorkspaceStats, HealthResponse } from '@/types';

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
    const total = totals?.total_documents ?? 0;
    const highRisk = totals?.high_risk ?? 0;
    const suspicious = totals?.requires_review ?? 0;
    const lowRisk = totals?.low_risk ?? 0;
    const other = total - highRisk - suspicious - lowRisk;

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

  // Dynamic SVG Donut Chart Component
  const DonutChart = () => {
    const radius = 45;
    const circumference = 2 * Math.PI * radius;

    const dashHigh = (stats.highPct / 100) * circumference;
    const dashSusp = (stats.suspPct / 100) * circumference;
    const dashLow = (stats.lowPct / 100) * circumference;

    return (
      <svg width="200" height="200" viewBox="0 0 200 200" className="mx-auto">
        <circle cx="100" cy="100" r={radius} fill="none" stroke="#30363d" strokeWidth="15" />
        {stats.total > 0 && (
          <>
            <circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke="#dc2626"
              strokeWidth="15"
              strokeDasharray={`${dashHigh} ${circumference}`}
              strokeDashoffset="0"
              strokeLinecap="round"
              transform="rotate(-90 100 100)"
            />
            <circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke="#d97706"
              strokeWidth="15"
              strokeDasharray={`${dashSusp} ${circumference}`}
              strokeDashoffset={-dashHigh}
              strokeLinecap="round"
              transform="rotate(-90 100 100)"
            />
            <circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke="#10b981"
              strokeWidth="15"
              strokeDasharray={`${dashLow} ${circumference}`}
              strokeDashoffset={-(dashHigh + dashSusp)}
              strokeLinecap="round"
              transform="rotate(-90 100 100)"
            />
          </>
        )}
        <text x="100" y="96" textAnchor="middle" className="text-2xl font-bold fill-white font-mono">
          {stats.total}
        </text>
        <text x="100" y="115" textAnchor="middle" className="text-[10px] fill-gray-400 uppercase tracking-widest">
          Documents
        </text>
      </svg>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end border-b border-ink-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Caseload Analytics</h1>
          <p className="text-sm text-gray-400 mt-1">
            Statistical breakdown of examined documents and risk assessments.
          </p>
        </div>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="p-2 bg-ink-panel border border-ink-border hover:bg-ink-hover rounded-sm text-xs text-gray-300 font-medium transition-colors"
          title="Refresh Analytics"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {error && <p role="alert" className="text-sm text-red-300">Analytics could not be loaded. Refresh to retry.</p>}
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Documents', value: stats.total, icon: Layers, color: 'text-brand' },
          { label: 'High Risk Documents', value: stats.highRisk, icon: ShieldAlert, color: 'text-red-400' },
          { label: 'Requires Review', value: stats.suspicious, icon: AlertTriangle, color: 'text-amber-400' },
          { label: 'Low Risk Documents', value: stats.lowRisk, icon: CheckCircle, color: 'text-emerald-400' },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label} variant="metrics" className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">{stat.label}</p>
                  <p className="text-2xl font-bold font-mono text-white">
                    {loading ? <Loader2 size={20} className="animate-spin text-brand" /> : totals ? stat.value : 'Unavailable'}
                  </p>
                </div>
                <div className="p-2 rounded-sm bg-ink-base border border-ink-border">
                  <Icon size={18} className={stat.color} />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Visual Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Donut */}
        <Card variant="evidence" title="Risk Classification Breakdown">
          <div className="p-6">
            <DonutChart />
            <div className="grid grid-cols-3 gap-2 mt-6 pt-4 border-t border-ink-border text-center">
              <div>
                <p className="text-xs font-bold text-red-400 font-mono">{stats.highPct}%</p>
                <p className="text-[10px] text-gray-400 uppercase mt-0.5">High Risk</p>
              </div>
              <div>
                <p className="text-xs font-bold text-amber-400 font-mono">{stats.suspPct}%</p>
                <p className="text-[10px] text-gray-400 uppercase mt-0.5">Review</p>
              </div>
              <div>
                <p className="text-xs font-bold text-emerald-400 font-mono">{stats.lowPct}%</p>
                <p className="text-[10px] text-gray-400 uppercase mt-0.5">Low Risk</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Format Distribution */}
        <Card variant="evidence" title="File formats · latest 100 exhibits">
          <div className="p-6 space-y-4">
            {stats.formatList.length === 0 ? (
              <p className="text-xs text-gray-500 text-center py-6">No documents recorded yet.</p>
            ) : (
              stats.formatList.map((item) => (
                <div key={item.label} className="space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-gray-200">{item.label} Documents</span>
                    <span className="font-mono text-gray-400">
                      {item.count} ({item.pct}%)
                    </span>
                  </div>
                  <div className="h-2 bg-ink-border rounded-sm overflow-hidden">
                    <div className="h-full bg-brand rounded-sm" style={{ width: `${item.pct}%` }} />
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Active Inspection Capabilities */}
        <Card variant="evidence" title="Active Analysis Capabilities">
          <ServiceHealthPanel health={health} />
        </Card>
      </div>
    </div>
  );
}
