import { useState, useEffect, useMemo } from 'react';
import { Search, FileText, ChevronRight, Loader2, FolderPlus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';
import { listDocuments, listCases } from '@/services/api';
import type { DocumentSummary, InvestigationCase } from '@/types';

export default function CasesPage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'ALL' | 'HIGH_RISK' | 'SUSPICIOUS' | 'LOW_RISK'>('ALL');

  const fetchCases = () => {
    setLoading(true);
    setError(false);
    Promise.all([listDocuments(100, 0), listCases()])
      .then(([data, caseData]) => {
        setCases(caseData);
        setDocuments(data || []);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const filteredDocs = useMemo(() => {
    return documents.filter((doc) => {
      if (selectedFilter !== 'ALL') {
        if (doc.unified_risk_tier !== selectedFilter) return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        doc.id.toLowerCase().includes(q) ||
        doc.original_filename.toLowerCase().includes(q) ||
        (doc.sha256_hash && doc.sha256_hash.toLowerCase().includes(q))
      );
    });
  }, [documents, selectedFilter, searchQuery]);

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

  const formatTimestamp = (iso?: string) => {
    if (!iso) return '-';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return iso;
    }
  };

  return (
    <div className="cases-page space-y-6">
      {error && <div role="alert" className="p-4 border border-red-400/30 rounded-xl text-red-300 text-sm">Unable to load the workspace. <button onClick={fetchCases} className="underline">Retry</button></div>}
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-ink-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Document Cases</h1>
          <p className="text-sm text-gray-400 mt-1">
            Browse your cases and the latest 100 evidence exhibits. Search applies to the loaded exhibits.
          </p>
        </div>
        <button
          onClick={() => navigate('/new')}
          className="px-4 py-2 bg-brand hover:bg-brand-hover text-white rounded-sm text-xs font-semibold flex items-center gap-2 shadow-sm transition-colors"
        >
          <FolderPlus size={15} /> Add New Document
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 justify-between items-stretch sm:items-center">
        {/* Risk Filter Tabs */}
        <div aria-label="Filter by risk" className="risk-filters flex gap-1.5 bg-ink-base p-1 rounded-lg border border-ink-border">
          {[
            { id: 'ALL', label: `All (${documents.length})` },
            { id: 'HIGH_RISK', label: `High Risk (${documents.filter(d => d.unified_risk_tier === 'HIGH_RISK').length})` },
            { id: 'SUSPICIOUS', label: `Review (${documents.filter(d => d.unified_risk_tier === 'SUSPICIOUS').length})` },
            { id: 'LOW_RISK', label: `Low Risk (${documents.filter(d => d.unified_risk_tier === 'LOW_RISK').length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedFilter(tab.id as typeof selectedFilter)}
              aria-pressed={selectedFilter === tab.id}
              className={`px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
                selectedFilter === tab.id
                  ? 'bg-brand text-white shadow-sm'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <section aria-label="Investigation cases" className="space-y-3">
        <h2 className="text-lg font-semibold">Investigation cases</h2>
        <p className="text-xs text-muted">Latest 100 cases visible to your account. Create a case with New investigation.</p>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{cases.map(item => <article key={item.id} className="p-5 rounded-xl border border-ink-border bg-ink-panel space-y-2">
          <div className="flex justify-between gap-2 text-[10px] text-muted"><span>{item.case_number}</span><span className="uppercase text-brand">{item.priority}</span></div>
          <h3 className="font-semibold text-sm">{item.title}</h3>
          {item.notes && <p className="text-xs text-muted whitespace-pre-wrap">{item.notes}</p>}
          <p className="text-xs text-muted">{item.document_count} exhibit(s) · {item.status}</p>
        </article>)}</div>
        {!loading && !error && cases.length === 0 && <p className="text-sm text-muted">No investigation cases yet.</p>}
      </section>
      {/* Search Input */}
        <div className="relative min-w-[280px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by filename or ID..."
            aria-label="Search documents by filename or ID"
            className="w-full pl-9 pr-3 py-1.5 bg-ink-base border border-ink-border rounded-sm text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand"
          />
        </div>
      </div>

      {/* Case Table Card */}
      <Card variant="evidence">
        {loading ? (
          <div className="p-16 text-center text-gray-400 flex flex-col items-center gap-2">
            <Loader2 size={24} className="animate-spin text-brand" />
            <span className="text-xs">Loading case database...</span>
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileText size={36} className="mx-auto text-gray-500 opacity-60" />
            <p className="text-sm font-semibold text-gray-300">No documents found matching criteria</p>
            <p className="text-xs text-gray-400">Try adjusting your search query or risk filter.</p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedFilter('ALL');
              }}
              className="px-3 py-1.5 bg-ink-panel hover:bg-ink-hover border border-ink-border rounded-sm text-xs font-semibold text-gray-300 mt-2"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-ink-base border-b border-ink-border text-gray-400 font-medium">
                <tr>
                  <th className="py-3 px-4">Document Exhibit</th>
                  <th className="py-3 px-3">Date Added</th>
                  <th className="py-3 px-3">Pages</th>
                  <th className="py-3 px-3">Final Assessment</th>
                  <th className="py-3 px-3 text-center">AI Forgery Score</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-border">
                {filteredDocs.map((doc) => {
                  const score = doc.composite_risk_score == null ? 'Unavailable' : `${Math.round(doc.composite_risk_score)}/100`;
                  return (
                    <tr
                      key={doc.id}
                      className="hover:bg-ink-hover/50 cursor-pointer transition-colors"
                      onClick={() => navigate(`/investigation/${doc.id}`)}
                    >
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white truncate max-w-[280px]">
                          {doc.original_filename}
                        </div>
                        <div className="text-[11px] text-gray-400 font-mono mt-0.5">
                          ID: {doc.id.slice(0, 8)}... | {doc.file_type.toUpperCase()}
                        </div>
                      </td>
                      <td className="py-3 px-3 text-gray-400 font-mono whitespace-nowrap">
                        {formatTimestamp(doc.created_at)}
                      </td>
                      <td className="py-3 px-3 text-gray-300 font-mono whitespace-nowrap">
                        {doc.page_count || 1} {doc.page_count === 1 ? 'page' : 'pages'}
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        {getAssessmentBadge(doc.unified_risk_tier)}
                      </td>
                      <td className="py-3 px-3 text-center whitespace-nowrap">
                        <span className="font-mono font-bold text-gray-200">
                          {score}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/investigation/${doc.id}`);
                          }}
                          className="px-3 py-1 bg-ink-panel hover:bg-brand hover:text-white border border-ink-border rounded-sm text-xs font-semibold text-gray-300 transition-colors inline-flex items-center gap-1"
                        >
                          Inspect <ChevronRight size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
