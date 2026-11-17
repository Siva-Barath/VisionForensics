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
        return <Badge variant="default" label="PENDING" size="sm" />;
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
    <div className="space-y-6">
      {documentsError && (
        <div role="alert" className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-2xl text-xs text-[#DC4545]">
          Recent exhibits could not be loaded. Please refresh the page to retry.
        </div>
      )}

      {/* Header with Quick Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-2">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7045E8] bg-[#F0EBFF] px-2.5 py-0.5 rounded-full border border-[#DDD5F9]">
              Forensic Operational Intelligence
            </span>
            <span className="text-[11px] font-semibold text-[#159B55] bg-[#EBF9F1] border border-[#D1F2DE] px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#159B55] animate-pulse" />
              Pilot Node Online
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#17172F]">Investigation Overview</h1>
          <p className="text-xs text-[#73758B] mt-0.5">
            Real-time casework status, forensic triage metrics, and rapid exhibit inspection.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/comparison')}
            className="px-4 py-2 bg-white hover:bg-[#F8F9FF] border border-[#E6E5F0] hover:border-[#DDD5F9] text-[#17172F] rounded-xl text-xs font-semibold transition-colors flex items-center gap-2 shadow-sm"
          >
            <GitCompare size={14} className="text-[#7045E8]" /> Compare Exhibits
          </button>
          <button 
            onClick={() => navigate('/new')}
            className="px-4 py-2 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-semibold transition-all flex items-center gap-2 shadow-md shadow-violet-200"
          >
            <FolderOpen size={14} /> New Investigation
          </button>
        </div>
      </div>

      {/* Primary KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 hover:border-[#DDD5F9] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#73758B]">Total Cases</span>
            <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
              <FileText size={18} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#17172F] font-mono">
            {totalAnalyzed ?? (loading ? '...' : '0')}
          </div>
          <p className="text-[11px] text-[#73758B]">Registered investigation dockets</p>
        </div>

        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 hover:border-[#D1F2DE] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#73758B]">Low Risk (Authentic)</span>
            <div className="w-9 h-9 rounded-xl bg-[#EBF9F1] text-[#159B55] flex items-center justify-center">
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#159B55] font-mono">
            {authenticCount ?? (loading ? '...' : '0')}
          </div>
          <p className="text-[11px] text-[#73758B]">Conforms to authentic document baselines</p>
        </div>

        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 hover:border-[#FFE8BF] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#73758B]">Requires Review</span>
            <div className="w-9 h-9 rounded-xl bg-[#FFF8EC] text-[#E9A12A] flex items-center justify-center">
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#E9A12A] font-mono">
            {reviewCount ?? (loading ? '...' : '0')}
          </div>
          <p className="text-[11px] text-[#73758B]">Borderline or conflicting track signals</p>
        </div>

        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 hover:border-[#FAD8D8] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#73758B]">High Risk (Tampering)</span>
            <div className="w-9 h-9 rounded-xl bg-[#FDF2F2] text-[#DC4545] flex items-center justify-center">
              <ShieldAlert size={18} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#DC4545] font-mono">
            {highRiskCount ?? (loading ? '...' : '0')}
          </div>
          <p className="text-[11px] text-[#73758B]">Substantial physical or ML forgery indicators</p>
        </div>
      </div>

      {/* Forensic Architecture Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-white border border-[#E6E5F0] rounded-2xl flex items-start gap-3.5 shadow-sm">
          <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
            <Cpu size={18} />
          </div>
          <div>
            <div className="text-xs font-bold text-[#17172F] uppercase tracking-wider">Track 1: Classical ML</div>
            <p className="text-[11px] text-[#73758B] mt-0.5 leading-relaxed">
              Random Forest with 18 physical features, evaluated against frozen decision boundary <strong className="text-[#7045E8] font-mono">T=0.40</strong>.
            </p>
          </div>
        </div>

        <div className="p-4 bg-white border border-[#E6E5F0] rounded-2xl flex items-start gap-3.5 shadow-sm">
          <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
            <ShieldCheck size={18} />
          </div>
          <div>
            <div className="text-xs font-bold text-[#17172F] uppercase tracking-wider">Track 2: Symbolic & Metadata</div>
            <p className="text-[11px] text-[#73758B] mt-0.5 leading-relaxed">
              PDF catalog validation, font mismatch auditing, cross-reference tables, and EXIF consistency.
            </p>
          </div>
        </div>

        <div className="p-4 bg-white border border-[#E6E5F0] rounded-2xl flex items-start gap-3.5 shadow-sm">
          <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
            <Layers size={18} />
          </div>
          <div>
            <div className="text-xs font-bold text-[#17172F] uppercase tracking-wider">Track 3: Visual & ELA</div>
            <p className="text-[11px] text-[#73758B] mt-0.5 leading-relaxed">
              Error Level Analysis (ELA) compression differentials and AKAZE keypoint copy-move duplicate detection.
            </p>
          </div>
        </div>
      </div>

      {/* Main Section: Recent Investigations & Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Investigations (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <h2 className="text-base font-bold text-[#17172F] flex items-center gap-2">
              <Clock size={16} className="text-[#7045E8]" /> Recent Case Exhibits
            </h2>
            <button
              onClick={() => navigate('/cases')}
              className="text-xs text-[#7045E8] hover:underline flex items-center gap-1 font-semibold"
            >
              View Full Archive ({documents.length}) <ChevronRight size={14} />
            </button>
          </div>

          <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-sm overflow-hidden">
            {/* Search & Filter Toolbar */}
            <div className="p-4 border-b border-[#E6E5F0] flex flex-col sm:flex-row items-center justify-between gap-3 bg-[#F8F9FF]">
              <div className="relative w-full sm:w-72">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#73758B]" />
                <input
                  type="text"
                  placeholder="Search exhibit filename or UUID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] font-mono shadow-sm"
                />
              </div>

              <div className="flex items-center gap-1.5 self-end sm:self-center">
                <Filter size={13} className="text-[#73758B] mr-1" />
                {(['ALL', 'HIGH_RISK', 'SUSPICIOUS', 'LOW_RISK'] as const).map((tier) => (
                  <button
                    key={tier}
                    onClick={() => setTierFilter(tier)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                      tierFilter === tier
                        ? 'bg-[#7045E8] text-white shadow-sm'
                        : 'bg-white hover:bg-[#F8F9FF] text-[#73758B] hover:text-[#17172F] border border-[#E6E5F0]'
                    }`}
                  >
                    {tier === 'ALL' ? 'All' : tier === 'HIGH_RISK' ? 'High' : tier === 'SUSPICIOUS' ? 'Review' : 'Low'}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="p-12 text-center text-[#73758B] flex flex-col items-center gap-2">
                <Loader2 size={24} className="animate-spin text-[#7045E8]" />
                <span className="text-xs">Loading case records...</span>
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="p-10 text-center space-y-3">
                <FileText size={32} className="mx-auto text-slate-300" />
                <p className="text-sm font-bold text-[#17172F]">No exhibits matching filter</p>
                <p className="text-xs text-[#73758B] max-w-sm mx-auto">
                  {documents.length === 0
                    ? 'Upload a PDF or image document to begin forensic analysis.'
                    : 'Try clearing your search query or filter selection.'}
                </p>
                {documents.length === 0 && (
                  <button
                    onClick={() => navigate('/new')}
                    className="px-4 py-2 bg-[#7045E8] text-white rounded-xl text-xs font-semibold mt-2 shadow-sm"
                  >
                    Start Investigation
                  </button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8F9FF] border-b border-[#E6E5F0] text-[#73758B] font-semibold uppercase text-[10px]">
                    <tr>
                      <th className="py-3 px-4">Exhibit & File Details</th>
                      <th className="py-3 px-3">Date Examined</th>
                      <th className="py-3 px-3">Final Assessment</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E6E5F0]">
                    {filteredDocuments.slice(0, 7).map((doc) => (
                      <tr 
                        key={doc.id}
                        className="hover:bg-[#F8F9FF] cursor-pointer transition-colors"
                        onClick={() => navigate(`/investigation/${doc.id}`)}
                      >
                        <td className="py-3.5 px-4">
                          <div className="font-bold text-[#17172F] truncate max-w-[240px]">
                            {doc.original_filename}
                          </div>
                          <div className="text-[11px] text-[#73758B] font-mono mt-0.5 flex items-center gap-2">
                            <span className="bg-[#F0EBFF] text-[#7045E8] px-1.5 py-0.2 rounded font-bold text-[10px]">
                              {doc.file_type.toUpperCase()}
                            </span>
                            <span>{doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}</span>
                            <span>•</span>
                            <span className="truncate max-w-[120px]" title={doc.id}>
                              {doc.id.slice(0, 8)}...
                            </span>
                          </div>
                        </td>
                        <td className="py-3.5 px-3 text-[#73758B] font-mono whitespace-nowrap text-xs">
                          {formatTimestamp(doc.created_at)}
                        </td>
                        <td className="py-3.5 px-3 whitespace-nowrap">
                          {getAssessmentBadge(doc.unified_risk_tier)}
                        </td>
                        <td className="py-3.5 px-4 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => {
                                const url = getReportDownloadUrl(doc.id);
                                window.open(url, '_blank');
                              }}
                              className="p-1.5 bg-white hover:bg-[#F0EBFF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-lg text-[#73758B] hover:text-[#7045E8] transition-colors"
                              title="Download Forensic PDF Dossier"
                            >
                              <Download size={13} />
                            </button>
                            <button
                              onClick={() => navigate(`/investigation/${doc.id}`)}
                              className="px-3 py-1.5 text-xs bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-lg font-semibold transition-all shadow-sm"
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
          </div>
        </div>

        {/* System Diagnostics & Health (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[#17172F] flex items-center gap-2">
              <Activity size={16} className="text-[#7045E8]" /> Analysis Engines
            </h2>
            <span className="text-[11px] font-mono font-bold text-[#159B55] bg-[#EBF9F1] border border-[#D1F2DE] px-2.5 py-0.5 rounded-full">
              {health?.status ?? 'Online'}
            </span>
          </div>

          <Card variant="evidence" className="p-5">
            <ServiceHealthPanel health={health} />
          </Card>

          {/* Quick Shortcuts */}
          <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#73758B] font-bold block">
              Forensic Navigation
            </span>
            <div className="space-y-2">
              <button
                onClick={() => navigate('/analytics')}
                className="w-full p-3 bg-[#F8F9FF] hover:bg-[#F0EBFF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-xl text-left text-xs font-bold text-[#17172F] flex items-center justify-between transition-colors"
              >
                <span>Caseload Analytics & Model Metrics</span>
                <ChevronRight size={14} className="text-[#73758B]" />
              </button>
              <button
                onClick={() => navigate('/comparison')}
                className="w-full p-3 bg-[#F8F9FF] hover:bg-[#F0EBFF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-xl text-left text-xs font-bold text-[#17172F] flex items-center justify-between transition-colors"
              >
                <span>Dual-Exhibit Differential Workspace</span>
                <ChevronRight size={14} className="text-[#73758B]" />
              </button>
              <button
                onClick={() => navigate('/reports')}
                className="w-full p-3 bg-[#F8F9FF] hover:bg-[#F0EBFF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-xl text-left text-xs font-bold text-[#17172F] flex items-center justify-between transition-colors"
              >
                <span>Tamper-Evident Dossier Archive</span>
                <ChevronRight size={14} className="text-[#73758B]" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
