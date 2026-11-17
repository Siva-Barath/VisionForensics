import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  AlertTriangle, 
  RefreshCw, 
  ArrowLeft, 
} from 'lucide-react';
import Card from '@/components/ui/Card';
import { DocumentIdentityHeader } from '../components/DocumentIdentityHeader';
import { InvestigationSummaryCard } from '../components/InvestigationSummaryCard';
import { MLIntelligenceSection } from '../components/MLIntelligenceSection';
import { WhyWeReachedAssessment } from '../components/WhyWeReachedAssessment';
import { InvestigationTimeline } from '../components/InvestigationTimeline';
import { DocumentPreviewCard } from '../components/DocumentPreviewCard';
import { AdvancedForensicEvidence } from '../components/AdvancedForensicEvidence';
import { GenerateReportModal } from '../components/GenerateReportModal';
import { Region } from '../types';
import { getDocumentAnalysis, getDocumentImageUrl, getDocumentCustodyLogs } from '@/services/api';
import { extractApiError } from '@/utils/helpers';
import type { DocumentAnalysisResponse } from '@/types';

export default function InvestigationDashboardPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState<DocumentAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [is404, setIs404] = useState(false);

  // Multi-page document navigation state
  const [currentPage, setCurrentPage] = useState<number>(0);

  // Forensic Report Modal State
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  // Evidence Custody Logs
  const [custodyLogs, setCustodyLogs] = useState<Array<any>>([]);
  const [custodyLoading, setCustodyLoading] = useState(false);

  // Active advanced detail tab
  const [advancedTab, setAdvancedTab] = useState<string>('ml');

  const fetchAnalysis = () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    setIs404(false);
    setAnalysis(null);

    getDocumentAnalysis(id)
      .then((data) => {
        setAnalysis(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setLoading(false);
        const errMsg = extractApiError(err);
        if (errMsg.toLowerCase().includes('not found') || errMsg.toLowerCase().includes('expired')) {
          setIs404(true);
          setError(`Forensic analysis for document ID '${id}' was not found or has expired.`);
        } else {
          setError(errMsg);
        }
      });
  };

  useEffect(() => {
    fetchAnalysis();
  }, [id]);

  useEffect(() => {
    if (id) {
      setCustodyLoading(true);
      getDocumentCustodyLogs(id)
        .then((logs) => setCustodyLogs(logs || []))
        .catch(() => setCustodyLogs([]))
        .finally(() => setCustodyLoading(false));
    }
  }, [id]);

  // Loading State
  if (loading) {
    return (
      <div className="max-w-xl mx-auto py-24 text-center space-y-4">
        <div className="w-12 h-12 border-3 border-[#7045E8] border-t-transparent rounded-full animate-spin mx-auto" />
        <h2 className="text-lg font-bold text-[#17172F] tracking-tight">
          Retrieving Forensic Investigation Findings
        </h2>
        <p className="text-xs text-[#73758B] font-mono">
          Loading calibrated analytical outputs for Exhibit: {id}
        </p>
      </div>
    );
  }

  // Error State
  if (error || !analysis) {
    return (
      <div className="max-w-xl mx-auto py-16 space-y-4">
        <Card variant="evidence" className="p-8 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-[#FDF2F2] border border-[#FAD8D8] flex items-center justify-center mx-auto text-[#DC4545]">
            <AlertTriangle size={28} />
          </div>
          <h2 className="text-lg font-bold text-[#17172F] tracking-tight">
            {is404 ? 'Investigation Not Found' : 'Unable to Retrieve Findings'}
          </h2>
          <p className="text-xs text-[#DC4545] font-mono bg-[#FDF2F2] border border-[#FAD8D8] p-3 rounded-xl leading-relaxed text-left">
            {error || 'An unexpected error occurred while communicating with the server.'}
          </p>

          <div className="flex justify-center gap-3 pt-3">
            <button
              onClick={() => navigate('/cases')}
              className="px-4 py-2 bg-white border border-[#E6E5F0] hover:bg-[#F8F9FF] text-[#17172F] rounded-xl text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft size={14} /> Back to Cases
            </button>
            <button
              onClick={fetchAnalysis}
              className="px-4 py-2 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm"
            >
              <RefreshCw size={14} /> Retry
            </button>
          </div>
        </Card>
      </div>
    );
  }

  // Genuine Forensic Regions
  const regions: Region[] = (analysis.detected_regions || []).map((r) => ({
    id: r.id,
    evidence_id: r.evidence_id,
    type: r.category,
    detector: r.detector,
    points: r.bounding_box.points,
    confidence: r.confidence ?? 1.0,
    severity: r.severity,
    description: r.description,
    page_index: r.page_index ?? 0,
  }));

  const pageCount = analysis.image_dimensions?.page_count || 1;
  const imageUrl = getDocumentImageUrl(analysis.document_id, currentPage);
  const heatmapUrl = analysis.heatmap_available_pages?.includes(currentPage)
    ? `/api/v1/documents/${analysis.document_id}/heatmap?page=${currentPage}`
    : null;

  return (
    <div className="space-y-6 pb-12">
      {/* ------------------------------------------------------------- */}
      {/* SECTION A: DOCUMENT IDENTITY HEADER                           */}
      {/* ------------------------------------------------------------- */}
      <DocumentIdentityHeader
        analysis={analysis}
        pageCount={pageCount}
        onOpenReportModal={() => setIsReportModalOpen(true)}
        onNavigateComparison={() => navigate(`/comparison?docA=${analysis.document_id}`)}
      />

      {/* ------------------------------------------------------------- */}
      {/* SECTION B: MAIN INVESTIGATION VERDICT BANNER CARD             */}
      {/* ------------------------------------------------------------- */}
      <InvestigationSummaryCard analysis={analysis} />

      {/* ------------------------------------------------------------- */}
      {/* SECTION C & D: TWO-COLUMN MAIN ANALYSIS AREA                  */}
      {/* ------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: ML Screening Result + Key Findings + Workflow (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Top Row: ML Screening Result + Key Findings */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <MLIntelligenceSection analysis={analysis} />
            <WhyWeReachedAssessment 
              analysis={analysis} 
              onSelectInsightTab={(tab) => setAdvancedTab(tab)}
            />
          </div>

          {/* Bottom Card: Investigation Workflow Stepper */}
          <InvestigationTimeline analysis={analysis} />
        </div>

        {/* RIGHT COLUMN: Document Preview Card (5 cols) */}
        <div className="lg:col-span-5 h-full">
          <DocumentPreviewCard
            imageUrl={imageUrl}
            heatmapUrl={heatmapUrl}
            regions={regions}
            currentPage={currentPage}
            pageCount={pageCount}
            onPageChange={setCurrentPage}
            originalFilename={analysis.original_filename}
          />
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* SECTION E: EXPLORE ADVANCED FORENSIC ANALYSIS (ACCORDION)     */}
      {/* ------------------------------------------------------------- */}
      <AdvancedForensicEvidence
        analysis={analysis}
        pageCount={pageCount}
        custodyLogs={custodyLogs}
        custodyLoading={custodyLoading}
        activeTab={advancedTab}
        onTabChange={setAdvancedTab}
        onPageSelect={setCurrentPage}
      />

      {/* Report Generation Modal */}
      {isReportModalOpen && (
        <GenerateReportModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          documentId={analysis.document_id || id || ''}
          documentFilename={analysis.original_filename}
          unifiedRiskTier={analysis.unified_risk_tier || 'LOW_RISK'}
          compositeScore={analysis.composite_risk_score ?? 25.2}
        />
      )}
    </div>
  );
}
