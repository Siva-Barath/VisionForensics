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
        return <Badge variant="default" label="PENDING" size="sm" />;
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
      {error && (
        <div role="alert" className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-2xl text-xs text-[#DC4545]">
          Unable to load the workspace. <button onClick={fetchCases} className="underline font-bold">Retry</button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-2 border-b border-[#E6E5F0]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#17172F]">Document Cases</h1>
          <p className="text-xs text-[#73758B] mt-0.5">
            Browse registered investigation dockets and recent evidence exhibits.
          </p>
        </div>
        <button
          onClick={() => navigate('/new')}
          className="px-4 py-2 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-sm transition-all"
        >
          <FolderPlus size={15} /> Add New Document
        </button>
      </div>

      {/* Case Dockets Cards Grid */}
      {cases.length > 0 && (
        <section aria-label="Investigation cases" className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-[#17172F]">Active Investigation Cases</h2>
            <span className="text-xs text-[#73758B] font-mono">{cases.length} cases registered</span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {cases.map((item) => (
              <article key={item.id} className="p-5 rounded-2xl border border-[#E6E5F0] bg-white space-y-2 shadow-sm hover:border-[#DDD5F9] transition-all">
                <div className="flex justify-between items-center gap-2 text-[11px] font-mono">
                  <span className="font-bold text-[#7045E8]">{item.case_number}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                    item.priority === 'urgent' ? 'bg-[#FFF8EC] text-[#E9A12A]' : 'bg-[#F0EBFF] text-[#7045E8]'
                  }`}>
                    {item.priority}
                  </span>
                </div>
                <h3 className="font-bold text-sm text-[#17172F]">{item.title}</h3>
                {item.notes && <p className="text-xs text-[#73758B] whitespace-pre-wrap leading-relaxed">{item.notes}</p>}
                <p className="text-xs text-[#73758B] pt-1 border-t border-[#E6E5F0]">{item.document_count} exhibit(s) • {item.status}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 justify-between items-stretch sm:items-center pt-2">
        {/* Risk Filter Tabs */}
        <div aria-label="Filter by risk" className="risk-filters flex gap-1.5 bg-[#F0EBFF] p-1 rounded-xl border border-[#DDD5F9]">
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
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                selectedFilter === tab.id
                  ? 'bg-[#7045E8] text-white shadow-sm'
                  : 'text-[#73758B] hover:text-[#17172F]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative min-w-[280px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#73758B]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by filename or ID..."
            aria-label="Search documents by filename or ID"
            className="w-full pl-9 pr-3 py-1.5 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-sm"
          />
        </div>
      </div>

      {/* Case Table Card */}
      <Card variant="evidence">
        {loading ? (
          <div className="p-16 text-center text-[#73758B] flex flex-col items-center gap-2">
            <Loader2 size={24} className="animate-spin text-[#7045E8]" />
            <span className="text-xs">Loading case database...</span>
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileText size={36} className="mx-auto text-slate-300" />
            <p className="text-sm font-bold text-[#17172F]">No documents found matching criteria</p>
            <p className="text-xs text-[#73758B]">Try adjusting your search query or risk filter.</p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedFilter('ALL');
              }}
              className="px-3.5 py-1.5 bg-white hover:bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl text-xs font-semibold text-[#17172F] mt-2 shadow-sm"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F8F9FF] border-b border-[#E6E5F0] text-[#73758B] font-semibold uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-4">Document Exhibit</th>
                  <th className="py-3 px-3">Date Added</th>
                  <th className="py-3 px-3">Pages</th>
                  <th className="py-3 px-3">Final Assessment</th>
                  <th className="py-3 px-3 text-center">AI Forgery Score</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E6E5F0]">
                {filteredDocs.map((doc) => {
                  const score = doc.composite_risk_score == null ? 'Unavailable' : `${Math.round(doc.composite_risk_score)}/100`;
                  return (
                    <tr
                      key={doc.id}
                      className="hover:bg-[#F8F9FF] cursor-pointer transition-colors"
                      onClick={() => navigate(`/investigation/${doc.id}`)}
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-[#17172F] truncate max-w-[280px]">
                          {doc.original_filename}
                        </div>
                        <div className="text-[11px] text-[#73758B] font-mono mt-0.5">
                          ID: {doc.id.slice(0, 8)}... | {doc.file_type.toUpperCase()}
                        </div>
                      </td>
                      <td className="py-3.5 px-3 text-[#73758B] font-mono whitespace-nowrap">
                        {formatTimestamp(doc.created_at)}
                      </td>
                      <td className="py-3.5 px-3 text-[#17172F] font-mono whitespace-nowrap">
                        {doc.page_count || 1} {doc.page_count === 1 ? 'page' : 'pages'}
                      </td>
                      <td className="py-3.5 px-3 whitespace-nowrap">
                        {getAssessmentBadge(doc.unified_risk_tier)}
                      </td>
                      <td className="py-3.5 px-3 text-center whitespace-nowrap">
                        <span className="font-mono font-bold text-[#17172F]">
                          {score}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/investigation/${doc.id}`);
                          }}
                          className="px-3 py-1.5 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1 shadow-sm"
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
