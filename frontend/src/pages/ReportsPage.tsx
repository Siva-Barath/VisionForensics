import { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { listReports, getReportDownloadUrl } from '@/services/api';
import type { ReportSummaryResponse } from '@/types';

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Investigation Reports</h1>
          <p className="text-sm text-gray-400 mt-2">
            Access, verify, and download tamper-evident forensic PDF case dossiers and exhibit records.
          </p>
        </div>
        <button
          onClick={fetchReports}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-ink-panel border border-ink-border hover:bg-ink-hover text-gray-300 rounded-sm text-xs font-bold transition-colors"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-lg flex items-center gap-3 text-xs text-red-300">
          <AlertCircle size={16} className="text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center p-12 text-center">
          <RefreshCw size={28} className="text-brand animate-spin mb-3" />
          <p className="text-xs text-gray-400 font-mono">Loading Forensic Reports Archive...</p>
        </div>
      ) : reports.length === 0 ? (
        <Card variant="evidence" className="p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-brand/10 border border-brand/30 flex items-center justify-center text-brand mx-auto mb-3">
            <FileText size={26} />
          </div>
          <h3 className="text-sm font-bold text-white mb-1">No Forensic Reports Generated Yet</h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto leading-relaxed">
            Open any completed investigation from the dashboard and click "Export Report" to generate
            a defense-grade tamper-evident PDF dossier.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {reports.map((r) => (
            <Card
              key={r.report_id}
              variant="evidence"
              className="hover:border-brand/50 transition-colors"
            >
              <div className="p-5">
                <div className="flex items-start justify-between gap-4">
                  {/* Report Info */}
                  <div className="flex items-start gap-4 flex-1 min-w-0">
                    <div className="w-12 h-12 rounded-sm bg-ink-border border border-ink-border flex items-center justify-center flex-shrink-0">
                      <FileText size={20} className="text-brand" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="case-id text-xs font-mono font-bold text-brand">
                          {r.report_number}
                        </span>
                        <span className="text-[10px] text-gray-400 font-mono">
                          Doc: {r.document_id.slice(0, 8)}...
                        </span>
                      </div>
                      <p className="text-sm font-bold text-gray-100 mb-1">{r.title}</p>
                      <div className="flex items-center gap-3 flex-wrap text-[11px] font-mono text-gray-400">
                        <span className="bg-ink-border px-2 py-0.5 rounded-sm text-gray-300">PDF</span>
                        <span>{(r.file_size_bytes / 1024).toFixed(1)} KB</span>
                        <span>{r.page_count} Pages</span>
                        <span className="truncate max-w-[200px]" title={r.sha256_hash}>
                          SHA-256: {r.sha256_hash.slice(0, 16)}...
                        </span>
                        <span>{r.created_at.slice(0, 10)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Risk & Actions */}
                  <div className="flex items-start gap-4 flex-shrink-0">
                    <div className="text-right">
                      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
                        Assessment
                      </p>
                      <Badge
                        label={r.unified_risk_tier}
                        variant={getRiskBadgeVariant(r.unified_risk_tier)}
                        size="sm"
                      />
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDownload(r.report_id)}
                        className="flex items-center gap-1.5 px-3 py-2 bg-brand hover:bg-brand-hover text-white rounded text-xs font-bold uppercase tracking-wider transition-colors shadow-sm"
                        title="Download Verified PDF"
                      >
                        <Download size={14} /> Download
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
