import { useState, useEffect, useMemo } from 'react';
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
  Search,
  Filter,
  Cpu,
  Layers,
  ShieldCheck,
  Download,
} from 'lucide-react';
import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';
import ServiceHealthPanel from '@/components/ServiceHealthPanel';
import { listDocuments, checkHealth, getWorkspaceStats, getReportDownloadUrl } from '@/services/api';
import type { DocumentSummary, HealthResponse, WorkspaceStats } from '@/types';

export default function HomePage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState(false);
  const [stats, setStats] = useState<WorkspaceStats | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [tierFilter, setTierFilter] = useState<'ALL' | 'HIGH_RISK' | 'SUSPICIOUS' | 'LOW_RISK'>('ALL');

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

  // Filtered documents list
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch = 
        doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.id.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesTier = 
        tierFilter === 'ALL' || doc.unified_risk_tier === tierFilter;
      return matchesSearch && matchesTier;
    });
  }, [documents, searchQuery, tierFilter]);

  return (
    <div className="dashboard-overview space-y-8">
      {documentsError && (
        <p role="alert" className="text-sm text-red-300 bg-red-950/30 border border-red-800 p-3 rounded-md">
          Recent exhibits could not be loaded. Refresh the page to retry.
        </p>
      )}

      {/* Header with Quick Actions */}
      <div className="overview-heading flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-brand font-semibold bg-brand/10 px-2 py-0.5 rounded-sm border border-brand/20">
              Forensic Operational Intelligence
            </span>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/60 px-2 py-0.5 rounded-sm flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Pilot Node Online
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Investigation Overview</h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time casework status, forensic triage metrics, and rapid exhibit inspection.
          </p>
        </div>
        <div className="overview-actions flex flex-wrap items-center gap-3">
          <button 
            onClick={() => navigate('/comparison')}
            className="px-4 py-2 bg-ink-panel hover:bg-ink-hover border border-ink-border text-gray-200 rounded-md text-sm font-semibold transition-colors flex items-center gap-2"
          >
            <GitCompare size={16} className="text-brand" /> Compare Exhibits
          </button>
          <button 
            onClick={() => navigate('/new')}
            className="px-4 py-2 bg-brand hover:bg-brand-hover text-white rounded-md text-sm font-semibold transition-colors flex items-center gap-2 shadow-md shadow-brand/20"
          >
            <FolderOpen size={16} /> New Investigation
          </button>
        </div>
      </div>

      {/* Primary Metrics: Triage Caseload */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card variant="metrics" className="p-5 hover:border-brand/50 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Cases</span>
            <div className="p-2 rounded-md bg-brand/10 border border-brand/20 text-brand">
              <FileText size={18} />
            </div>
          </div>
          <div className="metric-value text-3xl font-bold font-mono text-white mt-3">
            {totalAnalyzed ?? (loading ? '...' : '0')}
          </div>
          <p className="text-xs text-gray-400 mt-1">Registered investigation dockets</p>
        </Card>

        <Card variant="metrics" className="p-5 hover:border-emerald-500/50 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Low Risk (Authentic)</span>
            <div className="p-2 rounded-md bg-emerald-950/40 border border-emerald-800/60 text-emerald-400">
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div className="metric-value text-3xl font-bold font-mono text-emerald-400 mt-3">
            {authenticCount ?? (loading ? '...' : '0')}
          </div>
          <p className="text-xs text-emerald-400/80 mt-1">Conforms to authentic document baselines</p>
        </Card>

        <Card variant="metrics" className="p-5 hover:border-amber-500/50 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Requires Review</span>
            <div className="p-2 rounded-md bg-amber-950/40 border border-amber-800/60 text-amber-400">
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="metric-value text-3xl font-bold font-mono text-amber-400 mt-3">
            {reviewCount ?? (loading ? '...' : '0')}
          </div>
          <p className="text-xs text-amber-300/80 mt-1">Borderline or conflicting track signals</p>
        </Card>

        <Card variant="metrics" className="p-5 hover:border-red-500/50 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">High Risk (Tampering)</span>
            <div className="p-2 rounded-md bg-red-950/40 border border-red-800/60 text-red-400">
              <ShieldAlert size={18} />
            </div>
          </div>
          <div className="metric-value text-3xl font-bold font-mono text-red-400 mt-3">
            {highRiskCount ?? (loading ? '...' : '0')}
          </div>
          <p className="text-xs text-red-300/80 mt-1">Substantial physical or ML forgery indicators</p>
        </Card>
      </div>

      {/* Forensic Intelligence Architecture Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-ink-panel border border-ink-border rounded-md flex items-start gap-3">
          <div className="p-2 bg-brand/10 border border-brand/30 rounded text-brand shrink-0">
            <Cpu size={16} />
          </div>
          <div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Track 1: Classical ML</div>
            <p className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">
              Random Forest with 18 physical features, evaluated against frozen decision boundary <strong className="text-brand font-mono">T=0.40</strong>.
            </p>
          </div>
        </div>

        <div className="p-4 bg-ink-panel border border-ink-border rounded-md flex items-start gap-3">
          <div className="p-2 bg-brand/10 border border-brand/30 rounded text-brand shrink-0">
            <ShieldCheck size={16} />
          </div>
          <div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Track 2: Symbolic & Metadata</div>
            <p className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">
              PDF catalog validation, font mismatch auditing, cross-reference tables, and EXIF chronological consistency.
            </p>
          </div>
        </div>

        <div className="p-4 bg-ink-panel border border-ink-border rounded-md flex items-start gap-3">
          <div className="p-2 bg-brand/10 border border-brand/30 rounded text-brand shrink-0">
            <Layers size={16} />
          </div>
          <div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Track 3: Visual & ELA</div>
            <p className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">
              Error Level Analysis (ELA) compression differentials and AKAZE keypoint copy-move duplicate detection.
            </p>
          </div>
        </div>
      </div>

      {/* Main Section: Recent Investigations & System Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Investigations (2 columns) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock size={16} className="text-brand" /> Recent Case Exhibits
            </h2>
            <button
              onClick={() => navigate('/cases')}
              className="text-xs text-brand hover:underline flex items-center gap-1 font-semibold"
            >
              View Full Archive ({documents.length}) <ChevronRight size={14} />
            </button>
          </div>

          <Card variant="evidence">
            {/* Search and Filters Toolbar */}
            <div className="p-3 border-b border-ink-border flex flex-col sm:flex-row items-center justify-between gap-3 bg-ink-base/50">
              <div className="relative w-full sm:w-64">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search exhibit filename or UUID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 bg-ink-panel border border-ink-border rounded-md text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand font-mono"
                />
              </div>

              <div className="flex items-center gap-1.5 self-end sm:self-center">
                <Filter size={13} className="text-gray-400 mr-1" />
                {(['ALL', 'HIGH_RISK', 'SUSPICIOUS', 'LOW_RISK'] as const).map((tier) => (
                  <button
                    key={tier}
                    onClick={() => setTierFilter(tier)}
                    className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${
                      tierFilter === tier
                        ? 'bg-brand text-white'
                        : 'bg-ink-panel hover:bg-ink-hover text-gray-400 hover:text-gray-200 border border-ink-border'
                    }`}
                  >
                    {tier === 'ALL' ? 'All' : tier === 'HIGH_RISK' ? 'High' : tier === 'SUSPICIOUS' ? 'Review' : 'Low'}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="p-12 text-center text-gray-400 flex flex-col items-center gap-2">
                <Loader2 size={24} className="animate-spin text-brand" />
                <span className="text-xs">Loading case records...</span>
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="empty-investigations p-10 text-center space-y-3">
                <FileText size={32} className="mx-auto text-gray-500 opacity-60" />
                <p className="text-sm font-semibold text-gray-300">No exhibits matching filter</p>
                <p className="text-xs text-gray-400 max-w-sm mx-auto">
                  {documents.length === 0
                    ? 'Upload a PDF or image document to begin forensic analysis.'
                    : 'Try clearing your search query or filter selection.'}
                </p>
                {documents.length === 0 && (
                  <button
                    onClick={() => navigate('/new')}
                    className="px-4 py-2 bg-brand text-white rounded-md text-xs font-semibold mt-2"
                  >
                    Start Investigation
                  </button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-ink-base border-b border-ink-border text-gray-400 font-medium">
                    <tr>
                      <th className="py-3 px-4">Exhibit & File Details</th>
                      <th className="py-3 px-3">Date Examined</th>
                      <th className="py-3 px-3">Final Assessment</th>
                      <th className="py-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-border">
                    {filteredDocuments.slice(0, 7).map((doc) => (
                      <tr 
                        key={doc.id}
                        className="hover:bg-ink-hover/50 cursor-pointer transition-colors"
                        onClick={() => navigate(`/investigation/${doc.id}`)}
                      >
                        <td className="py-3 px-4">
                          <div className="font-semibold text-gray-200 truncate max-w-[240px]">
                            {doc.original_filename}
                          </div>
                          <div className="text-[11px] text-gray-400 font-mono mt-0.5 flex items-center gap-2">
                            <span className="bg-ink-border px-1.5 py-0.2 rounded text-gray-300">
                              {doc.file_type.toUpperCase()}
                            </span>
                            <span>{doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}</span>
                            <span className="text-gray-600">•</span>
                            <span className="text-gray-400 truncate max-w-[120px]" title={doc.id}>
                              {doc.id.slice(0, 8)}...
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-3 text-gray-400 font-mono whitespace-nowrap">
                          {formatTimestamp(doc.created_at)}
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          {getAssessmentBadge(doc.unified_risk_tier)}
                        </td>
                        <td className="py-3 px-3 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => {
                                const url = getReportDownloadUrl(doc.id);
                                window.open(url, '_blank');
                              }}
                              className="p-1.5 bg-ink-panel hover:bg-ink-hover border border-ink-border rounded text-gray-400 hover:text-white transition-colors"
                              title="Download Forensic PDF Dossier"
                            >
                              <Download size={13} />
                            </button>
                            <button
                              onClick={() => navigate(`/investigation/${doc.id}`)}
                              className="px-2.5 py-1 text-[11px] bg-brand hover:bg-brand-hover text-white rounded font-medium transition-colors"
                            >
                              Inspect
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        {/* System Diagnostics & Health (1 column) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Activity size={16} className="text-brand" /> Analysis Services
            </h2>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/60 px-2 py-0.5 rounded-sm">
              {health?.status ?? 'Online'}
            </span>
          </div>

          <Card variant="evidence" className="p-4">
            <ServiceHealthPanel health={health} />
          </Card>

          {/* Quick Shortcuts */}
          <Card variant="evidence" className="p-4 space-y-3">
            <span className="text-[11px] font-mono uppercase tracking-wider text-gray-400 font-bold block">
              Forensic Navigation
            </span>
            <div className="space-y-2">
              <button
                onClick={() => navigate('/analytics')}
                className="w-full p-2.5 bg-ink-base hover:bg-ink-hover border border-ink-border rounded-md text-left text-xs font-semibold text-gray-300 flex items-center justify-between transition-colors"
              >
                <span>Caseload Analytics & ML Model Metrics</span>
                <ChevronRight size={14} className="text-gray-500" />
              </button>
              <button
                onClick={() => navigate('/comparison')}
                className="w-full p-2.5 bg-ink-base hover:bg-ink-hover border border-ink-border rounded-md text-left text-xs font-semibold text-gray-300 flex items-center justify-between transition-colors"
              >
                <span>Dual-Exhibit Differential Workspace</span>
                <ChevronRight size={14} className="text-gray-500" />
              </button>
              <button
                onClick={() => navigate('/reports')}
                className="w-full p-2.5 bg-ink-base hover:bg-ink-hover border border-ink-border rounded-md text-left text-xs font-semibold text-gray-300 flex items-center justify-between transition-colors"
              >
                <span>Tamper-Evident Dossier Archive</span>
                <ChevronRight size={14} className="text-gray-500" />
              </button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}