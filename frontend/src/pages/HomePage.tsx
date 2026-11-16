import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FolderOpen,
  FileText,
  Clock,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Loader2,
  GitCompare,
  Activity,
} from 'lucide-react';
import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';
import ServiceHealthPanel from '@/components/ServiceHealthPanel';
import { listDocuments, checkHealth, getWorkspaceStats } from '@/services/api';
import type { DocumentSummary, HealthResponse, WorkspaceStats } from '@/types';

export default function HomePage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState(false);
  const [stats, setStats] = useState<WorkspaceStats | null>(null);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      listDocuments(50, 0).catch(() => { if (isMounted) setDocumentsError(true); return []; }),
      checkHealth().catch(() => null),
      getWorkspaceStats().catch(() => null),
    ]).then(([docs, healthData, statsData]) => {
      if (isMounted) {
        setDocuments(docs || []);
        setHealth(healthData);
        setStats(statsData);
        setLoading(false);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const totalAnalyzed = stats?.total_cases ?? null;
  const highRiskCount = stats?.high_risk ?? null;
  const reviewCount = stats?.requires_review ?? null;
  const authenticCount = stats?.examined_documents ?? null;

  const formatTimestamp = (iso?: string) => {
    if (!iso) return 'Recent';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return iso;
    }
  };

  const getAssessmentBadge = (tier?: string) => {
    switch (tier) {
      case 'HIGH_RISK':
        return <Badge variant="critical" label="HIGH RISK" size="sm" />;
      case 'SUSPICIOUS':
        return <Badge variant="high" label="REQUIRES REVIEW" size="sm" />;
      case 'LOW_RISK':
        return <Badge variant="verified" label="LOW RISK" size="sm" />;
      default:
        return <Badge variant="low" label="PENDING" size="sm" />;
    }
  };

  return (
    <div className="dashboard-overview space-y-8">
      {documentsError && <p role="alert" className="text-sm text-red-300">Recent exhibits could not be loaded. Refresh the page to retry.</p>}
      {/* Header with Actions */}
      <div className="overview-heading flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
        <div>
          <p className="eyebrow mb-3">Your workspace, at a glance</p>
          <h1 className="text-2xl font-bold tracking-tight text-white">Investigation overview</h1>
          <p className="text-sm text-gray-400 mt-1">
            A clear view of your documents, evidence, and next steps.
          </p>
        </div>
        <div className="overview-actions flex flex-wrap items-center gap-3">
          <button 
            onClick={() => navigate('/comparison')}
            className="px-4 py-2 bg-ink-panel hover:bg-ink-hover border border-ink-border text-gray-200 rounded-sm text-sm font-semibold transition-colors flex items-center gap-2"
          >
            <GitCompare size={16} /> Compare documents
          </button>
          <button 
            onClick={() => navigate('/new')}
            className="px-4 py-2 bg-brand hover:bg-brand-hover text-white rounded-sm text-sm font-semibold transition-colors flex items-center gap-2 shadow-sm"
          >
            <FolderOpen size={16} /> New investigation
          </button>
        </div>
      </div>

      {/* Primary Metrics: What investigators care about */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card variant="metrics" className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Cases</span>
            <FileText size={18} className="text-brand opacity-80" />
          </div>
          <div className="metric-value text-3xl font-bold text-white mt-2">{totalAnalyzed ?? '?'}</div>
          <p className="text-xs text-gray-400 mt-1">Investigation cases</p>
        </Card>

        <Card variant="metrics" className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Documents Examined</span>
            <CheckCircle2 size={18} className="text-emerald-400 opacity-80" />
          </div>
          <div className="metric-value text-3xl font-bold text-white mt-2">{authenticCount ?? '?'}</div>
          <p className="text-xs text-emerald-400/90 mt-1">Completed document analyses</p>
        </Card>

        <Card variant="metrics" className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Requires Review</span>
            <AlertTriangle size={18} className="text-amber-400 opacity-80" />
          </div>
          <div className="metric-value text-3xl font-bold text-amber-400 mt-2">{reviewCount ?? '?'}</div>
          <p className="text-xs text-amber-300/80 mt-1">Borderline or conflicting flags</p>
        </Card>

        <Card variant="metrics" className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">High Risk Documents</span>
            <ShieldAlert size={18} className="text-red-400 opacity-80" />
          </div>
          <div className="metric-value text-3xl font-bold text-red-400 mt-2">{highRiskCount ?? '?'}</div>
          <p className="text-xs text-red-300/80 mt-1">Significant manipulation indicators</p>
        </Card>
      </div>

      {/* Main Grid: Recent Investigations & Actual System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Investigations (2 columns) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock size={16} className="text-brand" /> Recent Investigations
            </h2>
            <button
              onClick={() => navigate('/cases')}
              className="text-xs text-brand hover:underline flex items-center gap-1 font-medium"
            >
              View All Documents <ChevronRight size={14} />
            </button>
          </div>

          <Card variant="evidence">
            {loading ? (
              <div className="p-12 text-center text-gray-400 flex flex-col items-center gap-2">
                <Loader2 size={24} className="animate-spin text-brand" />
                <span className="text-xs">Loading case records...</span>
              </div>
            ) : documents.length === 0 ? (
              <div className="empty-investigations p-10 text-center space-y-3">
                <FileText size={32} className="mx-auto text-gray-500 opacity-60" />
                <p className="text-sm font-semibold text-gray-300">Your next investigation starts here</p>
                <p className="text-xs text-gray-400 max-w-sm mx-auto">
                  Upload a PDF or image document to begin forensic analysis.
                </p>
                <button
                  onClick={() => navigate('/new')}
                  className="px-4 py-2 bg-brand text-white rounded-sm text-xs font-semibold mt-2"
                >
                  Start Investigation
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-ink-base border-b border-ink-border text-gray-400 font-medium">
                    <tr>
                      <th className="py-3 px-4">Document Name</th>
                      <th className="py-3 px-3">Date</th>
                      <th className="py-3 px-3">Final Assessment</th>
                      <th className="py-3 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-border">
                    {documents.slice(0, 6).map((doc) => (
                      <tr 
                        key={doc.id}
                        className="hover:bg-ink-hover/50 cursor-pointer transition-colors"
                        onClick={() => navigate(`/investigation/${doc.id}`)}
                      >
                        <td className="py-3 px-4">
                          <div className="font-semibold text-gray-200 truncate max-w-[240px]">
                            {doc.original_filename}
                          </div>
                          <div className="text-[11px] text-gray-400 font-mono mt-0.5">
                            ID: {doc.id.slice(0, 8)}... | {doc.file_type.toUpperCase()} ({doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'})
                          </div>
                        </td>
                        <td className="py-3 px-3 text-gray-400 font-mono whitespace-nowrap">
                          {formatTimestamp(doc.created_at)}
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          {getAssessmentBadge(doc.unified_risk_tier)}
                        </td>
                        <td className="py-3 px-3 text-right whitespace-nowrap">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/investigation/${doc.id}`);
                            }}
                            className="px-2.5 py-1 text-[11px] bg-ink-panel hover:bg-brand hover:text-white border border-ink-border rounded-sm text-gray-300 font-medium transition-colors"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        {/* Actual System Health (1 column) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Activity size={16} className="text-brand" /> Analysis services
            </h2>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/60 px-2 py-0.5 rounded-sm">
              {health?.status ?? 'Status unavailable'}
            </span>
          </div>

          <Card variant="evidence" className="p-4"><ServiceHealthPanel health={health} /></Card>
        </div>
      </div>
    </div>
  );
}
