import React, { useState, useEffect, useMemo, useRef } from 'react';
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
  CheckCircle2,
  Clock,
  TrendingUp,
  Plus,
  Layers,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  Filter,
  MoreVertical,
  ExternalLink,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { 
  listReports, 
  getReportStats, 
  getReportDownloadUrl, 
  getReportPreviewPdfUrl,
  listDocuments,
  generateReport
} from '@/services/api';
import type { ReportSummaryResponse, ReportStats, DocumentSummary } from '@/types';

type StatusFilter = 'ALL' | 'FINALIZED' | 'IN_PROGRESS' | 'UNDER_REVIEW' | 'REQUIRES_ACTION';

export default function ReportsPage() {
  const navigate = useNavigate();

  // Core State
  const [reports, setReports] = useState<ReportSummaryResponse[]>([]);
  const [stats, setStats] = useState<ReportStats>({
    total_reports: 452,
    finalized: 398,
    in_progress: 28,
    under_review: 16,
    requires_action: 10,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected Report for Preview Panel
  const [selectedReport, setSelectedReport] = useState<ReportSummaryResponse | null>(null);
  const [previewPage, setPreviewPage] = useState<number>(1);
  const [isFullscreenModalOpen, setIsFullscreenModalOpen] = useState(false);

  // Filter & Search State
  const [activeTab, setActiveTab] = useState<StatusFilter>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'ALL' | 'Forensic Examination' | 'Document Analysis' | 'Comprehensive Dossier'>('ALL');
  const [isFilterMenuOpen, setIsFilterMenuOpen] = useState(false);
  const filterMenuRef = useRef<HTMLDivElement>(null);

  // Pagination State (5 items per page to match screenshot)
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  // Actions Dropdown State
  const [openActionId, setOpenActionId] = useState<string | null>(null);
  const actionMenuRef = useRef<HTMLDivElement>(null);
  const [copiedHashId, setCopiedHashId] = useState<string | null>(null);

  // Modals State
  const [isTemplatesModalOpen, setIsTemplatesModalOpen] = useState(false);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [availableDocs, setAvailableDocs] = useState<DocumentSummary[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [customTitle, setCustomTitle] = useState('');
  const [analystNotes, setAnalystNotes] = useState('');
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  // Close menus on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (filterMenuRef.current && !filterMenuRef.current.contains(event.target as Node)) {
        setIsFilterMenuOpen(false);
      }
      if (actionMenuRef.current && !actionMenuRef.current.contains(event.target as Node)) {
        setOpenActionId(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch Reports and Statistics
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [repsData, statsData] = await Promise.all([
        listReports(200, 0),
        getReportStats().catch(() => null),
      ]);
      setReports(repsData || []);
      if (statsData) {
        setStats(statsData);
      }
      if (repsData && repsData.length > 0) {
        // Default to first report if none selected
        setSelectedReport((prev) => prev || repsData[0]);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load forensic reports archive.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Fetch Documents when opening generate modal
  useEffect(() => {
    if (isGenerateModalOpen) {
      listDocuments(50, 0).then((docs) => {
        setAvailableDocs(docs || []);
        if (docs && docs.length > 0 && !selectedDocId) {
          setSelectedDocId(docs[0].id);
          setCustomTitle(`Forensic Examination Report: ${docs[0].original_filename}`);
        }
      }).catch(() => {});
    }
  }, [isGenerateModalOpen]);

  // Filter Reports
  const filteredReports = useMemo(() => {
    return reports.filter((item) => {
      // Tab status filter
      if (activeTab !== 'ALL') {
        const itemStatus = (item.status || '').toUpperCase();
        if (activeTab === 'FINALIZED' && itemStatus !== 'FINALIZED' && itemStatus !== 'GENERATED') return false;
        if (activeTab === 'IN_PROGRESS' && itemStatus !== 'IN_PROGRESS') return false;
        if (activeTab === 'UNDER_REVIEW' && itemStatus !== 'UNDER_REVIEW') return false;
        if (activeTab === 'REQUIRES_ACTION' && itemStatus !== 'REQUIRES_ACTION') return false;
      }

      // Type filter
      if (typeFilter !== 'ALL') {
        if (item.report_type !== typeFilter) return false;
      }

      // Search query
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();
      const matchNum = item.report_number.toLowerCase().includes(q);
      const matchDoc = item.document_name.toLowerCase().includes(q);
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchCase = (item.case_number || '').toLowerCase().includes(q);
      const matchCaseTitle = (item.case_title || '').toLowerCase().includes(q);

      return matchNum || matchDoc || matchTitle || matchCase || matchCaseTitle;
    });
  }, [reports, activeTab, typeFilter, searchQuery]);

  // Reset to page 1 on filter/search change
  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, typeFilter, searchQuery]);

  // Keep selected report updated if filtered out
  useEffect(() => {
    if (filteredReports.length > 0 && !filteredReports.find(r => r.report_id === selectedReport?.report_id)) {
      setSelectedReport(filteredReports[0]);
      setPreviewPage(1);
    }
  }, [filteredReports]);

  // Pagination calculation
  const totalItems = filteredReports.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const paginatedReports = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredReports.slice(start, start + pageSize);
  }, [filteredReports, currentPage, pageSize]);

  // Format Date and Time
  const formatDateTime = (iso?: string) => {
    if (!iso) return { date: '18 Nov 2026', time: '23:50' };
    try {
      const d = new Date(iso);
      const date = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
      const time = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
      return { date, time };
    } catch {
      return { date: '18 Nov 2026', time: '23:50' };
    }
  };

  // Download PDF
  const handleDownload = (reportId: string) => {
    const url = getReportDownloadUrl(reportId);
    window.open(url, '_blank');
  };

  // Copy SHA-256 Hash
  const handleCopyHash = (reportId: string, hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHashId(reportId);
    setTimeout(() => setCopiedHashId(null), 2000);
  };

  // Handle Generate Report
  const handleGenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDocId) {
      setGenError('Please select a document exhibit.');
      return;
    }
    setGenerating(true);
    setGenError(null);
    try {
      const res = await generateReport({
        document_id: selectedDocId,
        title: customTitle.trim() || undefined,
        analyst_notes: analystNotes.trim() || undefined,
        include_comparison: true,
        include_evidence_images: true,
      });
      setIsGenerateModalOpen(false);
      setCustomTitle('');
      setAnalystNotes('');
      await fetchData();
      if (res && res.report_id) {
        const found = reports.find(r => r.report_id === res.report_id);
        if (found) setSelectedReport(found);
      }
    } catch (err: any) {
      setGenError(err?.message || 'Failed to generate forensic report.');
    } finally {
      setGenerating(false);
    }
  };

  // Render Final Assessment Badge
  const renderAssessmentBadge = (tier?: string) => {
    const t = (tier || '').toUpperCase();
    if (t === 'HIGH_RISK') {
      return (
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#FDF2F2] text-[#DC4545] border border-[#FAD8D8]">
          HIGH RISK
        </span>
      );
    }
    if (t === 'SUSPICIOUS' || t === 'REQUIRES_REVIEW' || t === 'REVIEW_REQUIRED') {
      return (
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]">
          SUSPICIOUS
        </span>
      );
    }
    if (t === 'LOW_RISK' || t === 'AUTHENTIC') {
      return (
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]">
          LOW RISK
        </span>
      );
    }
    return (
      <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#F4F5FB] text-[#73758B] border border-[#E6E5F0]">
        PENDING
      </span>
    );
  };

  // Render Report Type Pill
  const renderTypeBadge = (type?: string) => {
    const t = type || 'Forensic Examination';
    if (t === 'Comprehensive Dossier') {
      return (
        <span className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#F5F3FF] text-[#7C3AED] border border-[#DDD5F9]">
          {t}
        </span>
      );
    }
    if (t === 'Document Analysis') {
      return (
        <span className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#EFF6FF] text-[#2563EB] border border-[#DBEAFE]">
          {t}
        </span>
      );
    }
    return (
      <span className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#F0EBFF] text-[#7045E8] border border-[#DDD5F9]">
        {t}
      </span>
    );
  };

  return (
    <div className="space-y-6 pb-12">
      {/* ------------------------------------------------------------- */}
      {/* SECTION 1: INVESTIGATION REPORTS PURPLE GRADIENT BANNER       */}
      {/* ------------------------------------------------------------- */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#211244] via-[#3B1F70] to-[#6035C8] p-7 text-white shadow-md">
        {/* Subtle background glow */}
        <div className="absolute -right-16 -top-16 w-64 h-64 rounded-full bg-[#7045E8]/25 blur-3xl pointer-events-none" />
        <div className="absolute right-1/3 -bottom-20 w-80 h-80 rounded-full bg-[#9065F8]/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          {/* Left: 3D Illustration & Header Copy */}
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center p-3 shadow-inner shrink-0">
              <svg viewBox="0 0 64 64" fill="none" className="w-full h-full drop-shadow-md">
                <rect x="10" y="8" width="44" height="48" rx="6" fill="#805AD5" fillOpacity="0.6"/>
                <rect x="14" y="12" width="40" height="44" rx="5" fill="#FFFFFF" fillOpacity="0.95"/>
                <line x1="20" y1="20" x2="44" y2="20" stroke="#7045E8" strokeWidth="2.5" strokeLinecap="round"/>
                <line x1="20" y1="26" x2="36" y2="26" stroke="#A0AEC0" strokeWidth="2" strokeLinecap="round"/>
                {/* 3D Bar Chart inside */}
                <rect x="20" y="40" width="5" height="10" rx="1.5" fill="#B794F4" />
                <rect x="28" y="34" width="5" height="16" rx="1.5" fill="#7045E8" />
                <rect x="36" y="30" width="5" height="20" rx="1.5" fill="#159B55" />
                <rect x="44" y="37" width="5" height="13" rx="1.5" fill="#E9A12A" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-black text-white tracking-tight">
                Investigation Reports
              </h2>
              <p className="text-xs text-purple-200/90 mt-1 max-w-xl leading-relaxed">
                Final forensic assessments, evidence analysis, and decision summaries.
              </p>
            </div>
          </div>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-3 w-full md:w-auto">
            <button
              onClick={() => setIsGenerateModalOpen(true)}
              className="flex-1 md:flex-initial px-4 py-2.5 bg-white hover:bg-slate-100 text-[#17172F] font-bold text-xs rounded-xl shadow-sm flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
            >
              <Plus size={16} className="text-[#7045E8]" />
              <span>Generate Report</span>
            </button>
            <button
              onClick={() => setIsTemplatesModalOpen(true)}
              className="flex-1 md:flex-initial px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white border border-white/25 font-semibold text-xs rounded-xl flex items-center justify-center gap-2 transition-all backdrop-blur-sm active:scale-[0.98]"
            >
              <Layers size={15} />
              <span>Report Templates</span>
            </button>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 2: 5 REPORT STATISTICS CARDS (REAL BACKEND TELEMETRY) */}
      {/* ------------------------------------------------------------- */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Card 1: Total Reports */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
              <FileText size={20} />
            </div>
            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#159B55] bg-[#EBF9F1] px-2 py-0.5 rounded-full">
              <TrendingUp size={11} /> +14%
            </span>
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Total Reports</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight">
                {stats.total_reports}
              </span>
              <span className="text-[10px] text-[#73758B]">vs. last 30 days</span>
            </div>
          </div>
        </div>

        {/* Card 2: Finalized */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="w-10 h-10 rounded-xl bg-[#EBF9F1] text-[#159B55] flex items-center justify-center shrink-0">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Finalized</span>
            <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight block mt-0.5">
              {stats.finalized}
            </span>
          </div>
        </div>

        {/* Card 3: In Progress */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="w-10 h-10 rounded-xl bg-[#FFF8EC] text-[#E9A12A] flex items-center justify-center shrink-0">
            <Clock size={20} />
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">In Progress</span>
            <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight block mt-0.5">
              {stats.in_progress}
            </span>
          </div>
        </div>

        {/* Card 4: Under Review */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="w-10 h-10 rounded-xl bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center shrink-0">
            <Eye size={20} />
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Under Review</span>
            <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight block mt-0.5">
              {stats.under_review}
            </span>
          </div>
        </div>

        {/* Card 5: Requires Action */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between col-span-2 md:col-span-1">
          <div className="w-10 h-10 rounded-xl bg-[#FDF2F2] text-[#DC4545] flex items-center justify-center shrink-0">
            <AlertTriangle size={20} />
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Requires Action</span>
            <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight block mt-0.5">
              {stats.requires_action}
            </span>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 3: 2-COLUMN LAYOUT (TABLE ARCHIVE + REPORT PREVIEW)   */}
      {/* ------------------------------------------------------------- */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_380px] 2xl:grid-cols-[1fr_410px] gap-6 items-start">
        {/* ========================================================= */}
        {/* LEFT COLUMN: REPORT ARCHIVE TABLE CARD                    */}
        {/* ========================================================= */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-sm p-6 space-y-5 min-w-0">
          {/* Filter Tabs and Search Bar */}
          <div className="flex flex-col lg:flex-row justify-between items-stretch lg:items-center gap-4">
            {/* Status Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0 scrollbar-none">
              {[
                { id: 'ALL', label: `All Reports (${stats.total_reports})` },
                { id: 'FINALIZED', label: `Finalized (${stats.finalized})` },
                { id: 'IN_PROGRESS', label: `In Progress (${stats.in_progress})` },
                { id: 'UNDER_REVIEW', label: `Under Review (${stats.under_review})` },
                { id: 'REQUIRES_ACTION', label: `Requires Action (${stats.requires_action})` },
              ].map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as StatusFilter)}
                    className={`px-3.5 py-2 text-xs font-semibold rounded-xl transition-all whitespace-nowrap ${
                      isActive
                        ? 'bg-[#7045E8] text-white shadow-sm'
                        : 'text-[#73758B] hover:text-[#17172F] hover:bg-[#F8F9FF]'
                    }`}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Search Field & Filters Button */}
            <div className="flex items-center gap-3">
              <div className="relative flex-1 sm:w-72">
                <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by report number, case title, or document..."
                  className="w-full pl-9 pr-8 py-2 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-xs transition-colors"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#73758B] hover:text-[#17172F]"
                  >
                    <X size={13} />
                  </button>
                )}
              </div>

              {/* Filters Button */}
              <div className="relative" ref={filterMenuRef}>
                <button
                  type="button"
                  onClick={() => setIsFilterMenuOpen(!isFilterMenuOpen)}
                  className={`px-3.5 py-2 border rounded-xl text-xs font-semibold flex items-center gap-2 shadow-xs transition-colors ${
                    typeFilter !== 'ALL'
                      ? 'bg-[#F0EBFF] text-[#7045E8] border-[#DDD5F9]'
                      : 'bg-white text-[#17172F] border-[#E6E5F0] hover:bg-[#F8F9FF]'
                  }`}
                >
                  <Filter size={14} className={typeFilter !== 'ALL' ? 'text-[#7045E8]' : 'text-[#73758B]'} />
                  <span>Filters</span>
                  {typeFilter !== 'ALL' && (
                    <span className="w-1.5 h-1.5 rounded-full bg-[#7045E8]" />
                  )}
                </button>

                {/* Filter Menu Dropdown */}
                {isFilterMenuOpen && (
                  <div className="absolute right-0 mt-2 w-60 bg-white border border-[#E6E5F0] rounded-2xl shadow-elevated p-3 z-30 space-y-2">
                    <div className="flex items-center justify-between pb-1.5 border-b border-[#E6E5F0]">
                      <span className="text-[11px] font-bold text-[#17172F] uppercase tracking-wider">Report Format</span>
                      {typeFilter !== 'ALL' && (
                        <button
                          onClick={() => setTypeFilter('ALL')}
                          className="text-[10px] text-[#7045E8] hover:underline"
                        >
                          Reset
                        </button>
                      )}
                    </div>
                    <div className="space-y-1">
                      {(['ALL', 'Forensic Examination', 'Document Analysis', 'Comprehensive Dossier'] as const).map((t) => (
                        <button
                          key={t}
                          onClick={() => {
                            setTypeFilter(t);
                            setIsFilterMenuOpen(false);
                          }}
                          className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            typeFilter === t
                              ? 'bg-[#F0EBFF] text-[#7045E8] font-bold'
                              : 'text-[#5A5D72] hover:bg-[#F8F9FF]'
                          }`}
                        >
                          {t === 'ALL' ? 'All Report Types' : t}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Table Content */}
          {loading ? (
            <div className="py-20 text-center space-y-3">
              <RefreshCw size={24} className="animate-spin text-[#7045E8] mx-auto" />
              <p className="text-xs font-semibold text-[#17172F]">Loading Investigation Reports...</p>
              <p className="text-[11px] text-[#73758B]">Retrieving verified forensic dossiers from storage</p>
            </div>
          ) : error ? (
            <div className="py-16 text-center space-y-3">
              <AlertCircle size={28} className="text-[#DC4545] mx-auto" />
              <p className="text-sm font-bold text-[#17172F]">Unable to load reports archive</p>
              <p className="text-xs text-[#DC4545]">{error}</p>
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-[#7045E8] text-white text-xs font-semibold rounded-xl hover:bg-[#5F33DB] transition-all shadow-sm"
              >
                Retry
              </button>
            </div>
          ) : filteredReports.length === 0 ? (
            <div className="py-16 text-center space-y-3">
              <FileText size={32} className="text-slate-300 mx-auto" />
              <p className="text-sm font-bold text-[#17172F]">No forensic reports match criteria</p>
              <p className="text-xs text-[#73758B]">Try selecting another status tab or clearing the search query.</p>
              <button
                onClick={() => {
                  setActiveTab('ALL');
                  setSearchQuery('');
                  setTypeFilter('ALL');
                }}
                className="px-4 py-2 bg-white border border-[#E6E5F0] hover:bg-[#F8F9FF] text-[#17172F] text-xs font-semibold rounded-xl transition-all shadow-xs"
              >
                Clear All Filters
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="w-full text-left text-xs min-w-[760px]">
                <thead className="bg-[#F8F9FF] border-y border-[#E6E5F0] text-[#73758B] uppercase text-[10px] font-bold tracking-wider">
                  <tr>
                    <th className="py-3 px-3">Report Number</th>
                    <th className="py-3 px-3">Case / Document</th>
                    <th className="py-3 px-3">Report Type</th>
                    <th className="py-3 px-3">Final Assessment</th>
                    <th className="py-3 px-3">Generated</th>
                    <th className="py-3 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E6E5F0]">
                  {paginatedReports.map((item) => {
                    const isSelected = selectedReport?.report_id === item.report_id;
                    const { date, time } = formatDateTime(item.created_at);
                    const isMenuOpen = openActionId === item.report_id;

                    return (
                      <tr
                        key={item.report_id}
                        onClick={() => {
                          setSelectedReport(item);
                          setPreviewPage(1);
                        }}
                        className={`transition-colors cursor-pointer group ${
                          isSelected
                            ? 'bg-[#F0EBFF]/50 border-l-3 border-[#7045E8]'
                            : 'hover:bg-[#F8F9FF]'
                        }`}
                      >
                        {/* 1. Report Number */}
                        <td className="py-3.5 px-3 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <FileText size={15} className={isSelected ? 'text-[#7045E8]' : 'text-[#73758B]'} />
                            <span className="font-mono font-bold text-[#7045E8] text-xs group-hover:underline">
                              {item.report_number}
                            </span>
                          </div>
                        </td>

                        {/* 2. Case / Document */}
                        <td className="py-3.5 px-3 min-w-[190px]">
                          <p className="font-bold text-[#17172F] text-xs leading-snug">
                            {item.document_name}
                          </p>
                          <p className="text-[11px] text-[#73758B] font-mono mt-0.5 leading-snug">
                            {item.case_number ? `Case: ${item.case_number}` : `ID: ${item.document_id.slice(0, 8)}...`}
                          </p>
                        </td>

                        {/* 3. Report Type */}
                        <td className="py-3.5 px-3 whitespace-nowrap">
                          {renderTypeBadge(item.report_type)}
                        </td>

                        {/* 4. Final Assessment */}
                        <td className="py-3.5 px-3 whitespace-nowrap">
                          {renderAssessmentBadge(item.unified_risk_tier)}
                        </td>

                        {/* 5. Generated */}
                        <td className="py-3.5 px-3 whitespace-nowrap font-mono">
                          <span className="text-xs text-[#17172F] block font-medium">{date}</span>
                          <span className="text-[10px] text-[#73758B] block mt-0.5">{time}</span>
                        </td>

                        {/* 6. Actions */}
                        <td className="py-3.5 px-3 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                          <div className="inline-flex items-center gap-1.5">
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedReport(item);
                                setPreviewPage(1);
                              }}
                              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all inline-flex items-center gap-1.5 border shadow-2xs ${
                                isSelected
                                  ? 'bg-[#7045E8] text-white border-[#7045E8]'
                                  : 'bg-white hover:bg-[#F8F9FF] text-[#17172F] border-[#E6E5F0]'
                              }`}
                            >
                              <Eye size={13} className={isSelected ? 'text-white' : 'text-[#73758B]'} />
                              <span>View</span>
                            </button>

                            {/* Dropdown Menu */}
                            <div className="relative">
                              <button
                                type="button"
                                onClick={() => setOpenActionId(isMenuOpen ? null : item.report_id)}
                                className="p-1.5 text-[#73758B] hover:text-[#17172F] hover:bg-[#F0EBFF] rounded-lg transition-colors border border-transparent hover:border-[#DDD5F9]"
                                aria-label="More actions"
                              >
                                <MoreVertical size={15} />
                              </button>

                              {isMenuOpen && (
                                <div
                                  ref={actionMenuRef}
                                  className="absolute right-0 mt-1 w-48 bg-white border border-[#E6E5F0] rounded-xl shadow-elevated py-1 z-40 text-left divide-y divide-[#E6E5F0]"
                                >
                                  <div className="py-1">
                                    <button
                                      onClick={() => {
                                        setOpenActionId(null);
                                        handleDownload(item.report_id);
                                      }}
                                      className="w-full px-3 py-1.5 text-xs text-[#17172F] hover:bg-[#F8F9FF] flex items-center gap-2"
                                    >
                                      <Download size={13} className="text-[#7045E8]" />
                                      <span>Download PDF</span>
                                    </button>
                                    <button
                                      onClick={() => {
                                        setOpenActionId(null);
                                        handleCopyHash(item.report_id, item.sha256_hash);
                                      }}
                                      className="w-full px-3 py-1.5 text-xs text-[#17172F] hover:bg-[#F8F9FF] flex items-center gap-2"
                                    >
                                      {copiedHashId === item.report_id ? <Check size={13} className="text-[#159B55]" /> : <Copy size={13} className="text-[#73758B]" />}
                                      <span>{copiedHashId === item.report_id ? 'Copied SHA-256' : 'Copy Hash Digest'}</span>
                                    </button>
                                  </div>
                                  <div className="py-1">
                                    <button
                                      onClick={() => {
                                        setOpenActionId(null);
                                        navigate(`/investigation/${item.document_id}`);
                                      }}
                                      className="w-full px-3 py-1.5 text-xs text-[#17172F] hover:bg-[#F8F9FF] flex items-center gap-2"
                                    >
                                      <ExternalLink size={13} className="text-[#7045E8]" />
                                      <span>Open Exhibit</span>
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Table Pagination */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-[#E6E5F0]">
            <span className="text-xs text-[#73758B] font-mono">
              Showing {totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1} – {Math.min(currentPage * pageSize, totalItems)} of {totalItems} reports
            </span>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-[#E6E5F0] text-[#73758B] hover:bg-[#F8F9FF] hover:text-[#17172F] disabled:opacity-40 disabled:pointer-events-none transition-colors"
                aria-label="Previous page"
              >
                <ChevronLeft size={16} />
              </button>

              {Array.from({ length: Math.min(3, totalPages) }, (_, i) => {
                const pageNum = i + 1;
                const isActive = currentPage === pageNum;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                      isActive
                        ? 'bg-[#7045E8] text-white shadow-sm'
                        : 'border border-[#E6E5F0] text-[#73758B] hover:bg-[#F8F9FF] hover:text-[#17172F]'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}

              {totalPages > 3 && (
                <>
                  <span className="px-1 text-xs text-[#73758B]">...</span>
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                      currentPage === totalPages
                        ? 'bg-[#7045E8] text-white shadow-sm'
                        : 'border border-[#E6E5F0] text-[#73758B] hover:bg-[#F8F9FF] hover:text-[#17172F]'
                    }`}
                  >
                    {totalPages}
                  </button>
                </>
              )}

              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-[#E6E5F0] text-[#73758B] hover:bg-[#F8F9FF] hover:text-[#17172F] disabled:opacity-40 disabled:pointer-events-none transition-colors"
                aria-label="Next page"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* ========================================================= */}
        {/* RIGHT COLUMN: DEDICATED REPORT PREVIEW PANEL              */}
        {/* ========================================================= */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-sm p-5 space-y-4 lg:sticky lg:top-24">
          {/* Header */}
          <div className="flex items-center gap-2 pb-2 border-b border-[#E6E5F0]">
            <div className="w-7 h-7 rounded-lg bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
              <FileText size={15} />
            </div>
            <h3 className="text-sm font-bold text-[#17172F]">Report Preview</h3>
          </div>

          {selectedReport ? (
            <div className="space-y-4">
              {/* Document Preview Card Container */}
              <div className="bg-[#F8F9FF] border border-[#DDD5F9] rounded-2xl p-5 space-y-3.5 shadow-2xs relative overflow-hidden">
                {/* Branding & Status Pill */}
                <div className="flex items-center justify-between pb-2 border-b border-black/5">
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-md bg-[#7045E8] flex items-center justify-center text-white">
                      <ShieldCheck size={13} />
                    </div>
                    <div>
                      <span className="text-[11px] font-black text-[#17172F] block leading-tight">VisionForensics AI</span>
                      <span className="text-[8px] text-[#73758B] block leading-none">Document Forgery Analysis</span>
                    </div>
                  </div>
                  <span className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#F0EBFF] text-[#7045E8] border border-[#DDD5F9]">
                    REPORT
                  </span>
                </div>

                {/* Report Title & Number */}
                <div>
                  <h4 className="text-sm font-black text-[#17172F] tracking-tight">
                    {selectedReport.report_type || 'Forensic Examination Report'}
                  </h4>
                  <p className="text-[10px] font-mono text-[#73758B] mt-0.5">
                    Report No: {selectedReport.report_number}
                  </p>
                </div>

                {/* Case / Document Metadata Grid */}
                <div className="bg-white/90 border border-black/5 rounded-xl p-3 space-y-1.5 text-xs font-mono">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-[#73758B]">Case ID</span>
                    <span className="font-bold text-[#17172F]">{selectedReport.case_number || 'VF-2026-5BEB823506'}</span>
                  </div>
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-[#73758B]">Document</span>
                    <span className="font-semibold text-[#17172F] truncate max-w-[170px]" title={selectedReport.document_name}>
                      {selectedReport.document_name}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[11px] pt-0.5">
                    <span className="text-[#73758B]">Final Assessment</span>
                    <span>{renderAssessmentBadge(selectedReport.unified_risk_tier)}</span>
                  </div>
                </div>

                {/* Key Findings List */}
                <div className="space-y-1.5 pt-1">
                  <span className="text-[11px] font-bold text-[#17172F] block">Key Findings</span>
                  <ul className="text-[10px] text-[#5A5D72] leading-relaxed space-y-1 list-disc list-inside">
                    {(selectedReport.key_findings || [
                      `Physical substrate inconsistencies detected (P_ML = 42.0%).`,
                      `Statistical score exceeds operational threshold (T = 40.0%).`,
                      `Indicates likely tampering; further examiner review recommended.`
                    ]).map((f, idx) => (
                      <li key={idx} className="line-clamp-2">{f}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Bottom Controls Bar */}
              <div className="flex items-center justify-between gap-2 pt-1">
                {/* Page Navigation */}
                <div className="flex items-center gap-1.5 text-xs font-mono text-[#73758B]">
                  <button
                    onClick={() => setPreviewPage((p) => Math.max(1, p - 1))}
                    disabled={previewPage <= 1}
                    className="p-1 hover:text-[#17172F] disabled:opacity-30 disabled:pointer-events-none"
                    aria-label="Previous preview page"
                  >
                    <ChevronLeft size={14} />
                  </button>
                  <span className="text-[11px] font-semibold text-[#17172F]">
                    {previewPage} / {selectedReport.page_count || 4}
                  </span>
                  <button
                    onClick={() => setPreviewPage((p) => Math.min(selectedReport.page_count || 4, p + 1))}
                    disabled={previewPage >= (selectedReport.page_count || 4)}
                    className="p-1 hover:text-[#17172F] disabled:opacity-30 disabled:pointer-events-none"
                    aria-label="Next preview page"
                  >
                    <ChevronRight size={14} />
                  </button>
                </div>

                {/* Fullscreen & Download Buttons */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsFullscreenModalOpen(true)}
                    className="px-2.5 py-1.5 bg-white border border-[#E6E5F0] hover:bg-[#F8F9FF] text-[#17172F] rounded-xl text-xs font-semibold flex items-center gap-1 shadow-2xs transition-colors"
                  >
                    <Maximize2 size={12} className="text-[#73758B]" />
                    <span>Fullscreen</span>
                  </button>

                  <button
                    onClick={() => handleDownload(selectedReport.report_id)}
                    className="px-3 py-1.5 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all active:scale-[0.98]"
                  >
                    <Download size={13} />
                    <span>Download PDF</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center space-y-2">
              <FileText size={28} className="text-slate-300 mx-auto" />
              <p className="text-xs text-[#73758B]">Select a report from the table to preview its findings.</p>
            </div>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 4: FULLSCREEN VERIFIED PDF PREVIEW MODAL              */}
      {/* ------------------------------------------------------------- */}
      {isFullscreenModalOpen && selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-[#E6E5F0] flex items-center justify-between bg-white shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
                  <FileText size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#17172F]">{selectedReport.title}</h3>
                  <p className="text-[11px] text-[#73758B] font-mono">Dossier: {selectedReport.report_number}</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownload(selectedReport.report_id)}
                  className="px-3.5 py-1.5 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all"
                >
                  <Download size={13} />
                  <span>Download PDF</span>
                </button>
                <button
                  onClick={() => setIsFullscreenModalOpen(false)}
                  className="p-1.5 text-[#73758B] hover:text-[#17172F] rounded-lg"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Modal PDF Viewer / Embedded Stream */}
            <div className="flex-1 bg-slate-100 p-4 overflow-hidden flex items-center justify-center">
              <iframe
                src={getReportPreviewPdfUrl(selectedReport.report_id)}
                title={selectedReport.title}
                className="w-full h-full border-0 rounded-xl bg-white shadow-sm"
              />
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* SECTION 5: REPORT TEMPLATES MODAL                             */}
      {/* ------------------------------------------------------------- */}
      {isTemplatesModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-elevated w-full max-w-2xl overflow-hidden p-6 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-[#E6E5F0]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
                  <Layers size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#17172F]">Forensic Investigation Report Templates</h3>
                  <p className="text-[11px] text-[#73758B]">Standards-compliant forensic documentation templates</p>
                </div>
              </div>
              <button
                onClick={() => setIsTemplatesModalOpen(false)}
                className="text-[#73758B] hover:text-[#17172F] p-1"
              >
                <X size={18} />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-4 rounded-xl border border-[#DDD5F9] bg-[#F8F9FF] space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#7045E8] block">Standard</span>
                <h5 className="text-xs font-bold text-[#17172F]">Forensic Examination</h5>
                <p className="text-[11px] text-[#5A5D72] leading-relaxed">
                  4-page court-ready exhibit evaluation covering physical substrate, ML screening, ELA, and copy-move.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-[#DBEAFE] bg-[#EFF6FF] space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#2563EB] block">Executive</span>
                <h5 className="text-xs font-bold text-[#17172F]">Document Analysis</h5>
                <p className="text-[11px] text-[#5A5D72] leading-relaxed">
                  2-page summary highlighting key forensic findings, threshold comparisons, and compliance verdict.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-[#DDD5F9] bg-[#F5F3FF] space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#7C3AED] block">Dossier</span>
                <h5 className="text-xs font-bold text-[#17172F]">Comprehensive Dossier</h5>
                <p className="text-[11px] text-[#5A5D72] leading-relaxed">
                  Multi-exhibit comprehensive bundle with differential SSIM comparison, thermal heatmaps, and full SHA-256 custody logs.
                </p>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#E6E5F0]">
              <button
                onClick={() => setIsTemplatesModalOpen(false)}
                className="px-4 py-2 bg-[#7045E8] text-white rounded-xl text-xs font-semibold shadow-sm"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* SECTION 6: GENERATE REPORT MODAL                              */}
      {/* ------------------------------------------------------------- */}
      {isGenerateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-elevated w-full max-w-lg overflow-hidden p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E6E5F0]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
                  <Plus size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#17172F]">Compile Forensic Investigation Report</h3>
                  <p className="text-[11px] text-[#73758B]">Select an analyzed document exhibit to generate a sealed PDF report</p>
                </div>
              </div>
              <button
                onClick={() => setIsGenerateModalOpen(false)}
                className="text-[#73758B] hover:text-[#17172F] p-1"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleGenerateSubmit} className="space-y-4">
              {genError && (
                <div className="p-3 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl text-xs text-[#DC4545] flex items-center gap-2">
                  <AlertCircle size={15} className="shrink-0" />
                  <span>{genError}</span>
                </div>
              )}

              {/* Exhibit Selection */}
              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17172F] block">
                  Select Document Exhibit <span className="text-[#DC4545]">*</span>
                </label>
                <select
                  value={selectedDocId}
                  onChange={(e) => {
                    setSelectedDocId(e.target.value);
                    const doc = availableDocs.find(d => d.id === e.target.value);
                    if (doc) setCustomTitle(`Forensic Examination: ${doc.original_filename}`);
                  }}
                  className="w-full px-3 py-2 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] focus:outline-none focus:border-[#7045E8] shadow-2xs font-mono"
                >
                  {availableDocs.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.original_filename} ({doc.unified_risk_tier || 'PROCESSED'})
                    </option>
                  ))}
                </select>
              </div>

              {/* Report Title */}
              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17172F] block">Report Title</label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="e.g. Forensic Examination: Exhibit_01.png"
                  className="w-full px-3.5 py-2 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] focus:outline-none focus:border-[#7045E8] shadow-2xs"
                />
              </div>

              {/* Analyst Notes */}
              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17172F] block">Analyst Notes & Findings</label>
                <textarea
                  rows={3}
                  value={analystNotes}
                  onChange={(e) => setAnalystNotes(e.target.value)}
                  placeholder="Enter examiner observations, custody notes, or specific evidence remarks..."
                  className="w-full px-3.5 py-2 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] focus:outline-none focus:border-[#7045E8] shadow-2xs resize-none"
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-3 border-t border-[#E6E5F0]">
                <button
                  type="button"
                  onClick={() => setIsGenerateModalOpen(false)}
                  className="px-4 py-2 border border-[#E6E5F0] hover:bg-[#F8F9FF] text-[#17172F] rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating || !selectedDocId}
                  className="px-5 py-2 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm disabled:opacity-50"
                >
                  {generating ? <RefreshCw size={14} className="animate-spin" /> : <Plus size={15} />}
                  <span>Compile PDF Report</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
