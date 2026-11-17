import { useState, useEffect, useMemo } from 'react';
import {
  FileText,
  Download,
  RefreshCw,
  AlertCircle,
  Search,
  Eye,
  X,
  Copy,
  Check,
  ShieldCheck,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { listReports, getReportDownloadUrl } from '@/services/api';
import type { ReportSummaryResponse } from '@/types';

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedReport, setSelectedReport] = useState<ReportSummaryResponse | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listReports();
      setReports(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch forensic reports archive.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const getRiskBadgeVariant = (tier: string) => {
    switch (tier) {
      case 'HIGH_RISK':
        return 'critical';
      case 'SUSPICIOUS':
        return 'high';
      case 'LOW_RISK':
        return 'verified';
      default:
        return 'low';
    }
  };

  const handleDownload = (reportId: string) => {
    const url = getReportDownloadUrl(reportId);
    window.open(url, '_blank');
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const filteredReports = useMemo(() => {
    return reports.filter((r) => {
      const q = searchQuery.toLowerCase();
      return (
        r.title.toLowerCase().includes(q) ||
        r.report_number.toLowerCase().includes(q) ||
        r.document_id.toLowerCase().includes(q) ||
        r.sha256_hash.toLowerCase().includes(q)
      );
    });
  }, [reports, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-ink-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[11px] font-mono uppercase tracking-wider text-brand font-semibold bg-brand/10 px-2 py-0.5 rounded-sm border border-brand/20">
              Chain-of-Custody Archive
            </span>
            <span className="text-[11px] font-mono text-gray-400">Cryptographically Sealed PDF Dossiers</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Investigation Reports</h1>
          <p className="text-sm text-gray-400 mt-1">
            Access, inspect, and download tamper-evident forensic PDF case dossiers with immutable SHA-256 custody digests.
          </p>
        </div>
        <button
          onClick={fetchReports}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 bg-ink-panel border border-ink-border hover:bg-ink-hover text-gray-300 rounded-md text-xs font-semibold transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Dossiers</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-lg flex items-center gap-3 text-xs text-red-300">
          <AlertCircle size={16} className="text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-full max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by case title, report number, or document UUID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-ink-panel border border-ink-border rounded-md text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand font-mono"
          />
        </div>
        <span className="text-xs text-gray-400 font-mono hidden sm:inline">
          {filteredReports.length} {filteredReports.length === 1 ? 'dossier' : 'dossiers'} found
        </span>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center p-16 text-center">
          <RefreshCw size={32} className="text-brand animate-spin mb-3" />
          <p className="text-xs text-gray-400 font-mono">Querying Forensic Reports Ledger...</p>
        </div>
      ) : filteredReports.length === 0 ? (
        <Card variant="evidence" className="p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-brand/10 border border-brand/30 flex items-center justify-center text-brand mx-auto mb-3">
            <FileText size={26} />
          </div>
          <h3 className="text-sm font-bold text-white mb-1">
            {reports.length === 0 ? 'No Forensic Reports Generated Yet' : 'No Matching Reports Found'}
          </h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto leading-relaxed">
            {reports.length === 0
              ? 'Open any completed document investigation and click "Export Report" to generate an immutable, tamper-evident PDF dossier.'
              : 'Try clearing your search query to see all generated dossiers.'}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredReports.map((r) => (
            <Card
              key={r.report_id}
              variant="evidence"
              className="hover:border-brand/50 transition-all p-5"
            >
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                {/* Report Info */}
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  <div className="w-12 h-12 rounded-md bg-brand/10 border border-brand/20 flex items-center justify-center flex-shrink-0 text-brand">
                    <FileText size={24} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono font-bold text-brand bg-brand/10 px-2 py-0.5 rounded border border-brand/20">
                        {r.report_number}
                      </span>
                      <span className="text-[11px] text-gray-400 font-mono">
                        Doc: {r.document_id.slice(0, 8)}...
                      </span>
                    </div>
                    <p className="text-base font-bold text-gray-100 truncate mb-1">{r.title}</p>
                    <div className="flex items-center gap-3 flex-wrap text-[11px] font-mono text-gray-400">
                      <span className="bg-ink-border px-2 py-0.5 rounded text-gray-300">PDF DOSSIER</span>
                      <span>{(r.file_size_bytes / 1024).toFixed(1)} KB</span>
                      <span>•</span>
                      <span>{r.page_count} {r.page_count === 1 ? 'Page' : 'Pages'}</span>
                      <span>•</span>
                      <span className="truncate max-w-[200px]" title={r.sha256_hash}>
                        SHA-256: {r.sha256_hash.slice(0, 16)}...
                      </span>
                      <span>•</span>
                      <span>{r.created_at.slice(0, 10)}</span>
                    </div>
                  </div>
                </div>

                {/* Risk & Actions */}
                <div className="flex items-center justify-between lg:justify-end w-full lg:w-auto gap-4 pt-3 lg:pt-0 border-t lg:border-t-0 border-ink-border">
                  <div className="text-left lg:text-right">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
                      Final Assessment
                    </p>
                    <Badge
                      label={r.unified_risk_tier}
                      variant={getRiskBadgeVariant(r.unified_risk_tier)}
                      size="sm"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setSelectedReport(r)}
                      className="flex items-center gap-1.5 px-3 py-2 bg-ink-panel hover:bg-ink-hover border border-ink-border text-gray-200 rounded-md text-xs font-semibold transition-colors"
                      title="Inspect Dossier Metadata"
                    >
                      <Eye size={14} /> Details
                    </button>
                    <button
                      onClick={() => handleDownload(r.report_id)}
                      className="flex items-center gap-1.5 px-3 py-2 bg-brand hover:bg-brand-hover text-white rounded-md text-xs font-bold uppercase tracking-wider transition-colors shadow-sm"
                      title="Download Verified PDF"
                    >
                      <Download size={14} /> Download PDF
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Report Details Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-ink-panel border border-ink-border rounded-lg max-w-xl w-full p-6 space-y-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedReport(null)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white"
            >
              <X size={18} />
            </button>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <ShieldCheck size={18} className="text-brand" />
                <span className="text-xs font-mono uppercase tracking-wider text-brand font-bold">
                  Verified Forensic Dossier
                </span>
              </div>
              <h2 className="text-xl font-bold text-white">{selectedReport.title}</h2>
              <p className="text-xs text-gray-400 font-mono">Dossier #{selectedReport.report_number}</p>
            </div>

            <div className="space-y-3 text-xs bg-ink-base border border-ink-border rounded-md p-4 font-mono">
              <div className="flex justify-between py-1.5 border-b border-ink-border">
                <span className="text-gray-400 font-sans">Exhibit Document ID</span>
                <span className="text-white truncate max-w-[280px]" title={selectedReport.document_id}>
                  {selectedReport.document_id}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-ink-border">
                <span className="text-gray-400 font-sans">Final Classification</span>
                <span className="text-white font-bold">
                  {selectedReport.unified_risk_tier}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-ink-border">
                <span className="text-gray-400 font-sans">Dossier Size & Pages</span>
                <span className="text-white">
                  {(selectedReport.file_size_bytes / 1024).toFixed(1)} KB ({selectedReport.page_count} pages)
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-ink-border">
                <span className="text-gray-400 font-sans">Creation Date</span>
                <span className="text-white">{selectedReport.created_at}</span>
              </div>
              <div className="py-1.5 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 font-sans">Immutable SHA-256 Digest</span>
                  <button
                    onClick={() => handleCopyHash(selectedReport.sha256_hash)}
                    className="text-[11px] text-brand hover:underline flex items-center gap-1 font-sans"
                  >
                    {copiedHash ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                    {copiedHash ? 'Copied' : 'Copy Hash'}
                  </button>
                </div>
                <div className="text-[11px] text-emerald-400 break-all bg-ink-panel p-2 rounded border border-ink-border">
                  {selectedReport.sha256_hash}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setSelectedReport(null)}
                className="px-4 py-2 bg-ink-base hover:bg-ink-hover border border-ink-border text-gray-300 rounded-md text-xs font-semibold"
              >
                Close
              </button>
              <button
                onClick={() => handleDownload(selectedReport.report_id)}
                className="px-5 py-2 bg-brand hover:bg-brand-hover text-white rounded-md text-xs font-bold flex items-center gap-2"
              >
                <Download size={14} /> Download PDF Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}