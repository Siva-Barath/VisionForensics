import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  Folder, 
  Plus, 
  Download, 
  Search, 
  Filter, 
  Play, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  ArrowRight, 
  MoreVertical, 
  ChevronLeft, 
  ChevronRight, 
  X, 
  Files, 
  TrendingUp,
  RefreshCw,
  ExternalLink,
  FileCheck
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { listCases, getCaseStats, createCase } from '@/services/api';
import type { InvestigationCase, CaseStats } from '@/types';

type StatusFilter = 'ALL' | 'ACTIVE' | 'UNDER_REVIEW' | 'COMPLETED' | 'ESCALATED';

export default function CasesPage() {
  const navigate = useNavigate();

  // State Management
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [stats, setStats] = useState<CaseStats>({
    total_cases: 126,
    active: 8,
    under_review: 12,
    completed: 98,
    escalated: 8,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Filter & Search State
  const [activeTab, setActiveTab] = useState<StatusFilter>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<'ALL' | 'ROUTINE' | 'URGENT' | 'HIGH'>('ALL');
  const [isFilterMenuOpen, setIsFilterMenuOpen] = useState(false);
  const filterMenuRef = useRef<HTMLDivElement>(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  // New Case Modal State
  const [isNewCaseModalOpen, setIsNewCaseModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [newPriority, setNewPriority] = useState<'ROUTINE' | 'URGENT' | 'HIGH'>('ROUTINE');
  const [newStatus, setNewStatus] = useState<string>('ACTIVE');
  const [submittingCase, setSubmittingCase] = useState(false);
  const [caseError, setCaseError] = useState<string | null>(null);

  // Row Action Dropdown State
  const [openActionId, setOpenActionId] = useState<string | null>(null);
  const actionMenuRef = useRef<HTMLDivElement>(null);

  // Click outside to close menus
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

  // Fetch Cases and Stats
  const fetchData = async () => {
    setLoading(true);
    setError(false);
    try {
      const [caseData, statsData] = await Promise.all([
        listCases(),
        getCaseStats().catch(() => null),
      ]);
      setCases(caseData || []);
      if (statsData) {
        setStats(statsData);
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter Cases
  const filteredCases = useMemo(() => {
    return cases.filter((item) => {
      // Tab status filter
      if (activeTab !== 'ALL') {
        const itemStatus = (item.status || '').toUpperCase();
        if (activeTab === 'ACTIVE' && itemStatus !== 'ACTIVE' && itemStatus !== 'OPEN') return false;
        if (activeTab === 'UNDER_REVIEW' && !['IN_REVIEW', 'UNDER_REVIEW', 'REVIEW'].includes(itemStatus)) return false;
        if (activeTab === 'COMPLETED' && !['COMPLETED', 'CLOSED'].includes(itemStatus)) return false;
        if (activeTab === 'ESCALATED' && !['ESCALATED', 'FLAGGED'].includes(itemStatus)) return false;
      }

      // Priority filter
      if (priorityFilter !== 'ALL') {
        if ((item.priority || '').toUpperCase() !== priorityFilter) return false;
      }

      // Search query
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();
      const matchNum = item.case_number.toLowerCase().includes(q);
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchNotes = (item.notes || '').toLowerCase().includes(q);
      const matchExhibit = (item.exhibit_filenames || []).some(fn => fn.toLowerCase().includes(q));

      return matchNum || matchTitle || matchNotes || matchExhibit;
    });
  }, [cases, activeTab, priorityFilter, searchQuery]);

  // Pagination calculation
  const totalItems = filteredCases.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const paginatedCases = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredCases.slice(start, start + pageSize);
  }, [filteredCases, currentPage, pageSize]);

  // Reset to page 1 on filter/search change
  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, priorityFilter, searchQuery]);

  // Handle Create New Case
  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      setCaseError('Please enter a case title.');
      return;
    }
    setSubmittingCase(true);
    setCaseError(null);
    try {
      await createCase({
        title: newTitle.trim(),
        notes: newNotes.trim() || undefined,
        priority: newPriority,
        status: newStatus,
      });
      setIsNewCaseModalOpen(false);
      setNewTitle('');
      setNewNotes('');
      setNewPriority('ROUTINE');
      setNewStatus('ACTIVE');
      await fetchData();
    } catch {
      setCaseError('Failed to create case docket. Please verify inputs.');
    } finally {
      setSubmittingCase(false);
    }
  };

  // Handle Export Case List as CSV
  const handleExportCases = () => {
    if (cases.length === 0) return;
    const headers = ['Case ID', 'Case Title', 'Description', 'Priority', 'Status', 'Final Assessment', 'Exhibits', 'Created At'];
    const rows = filteredCases.map((c) => [
      `"${c.case_number}"`,
      `"${c.title.replace(/"/g, '""')}"`,
      `"${(c.notes || '').replace(/"/g, '""')}"`,
      `"${c.priority}"`,
      `"${c.status}"`,
      `"${c.final_assessment || 'PENDING'}"`,
      c.document_count || 1,
      `"${c.created_at || ''}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `VisionForensics_Cases_Export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

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

  // Render Status Badge
  const renderStatusBadge = (status?: string) => {
    const s = (status || 'ACTIVE').toUpperCase();
    if (s === 'ACTIVE' || s === 'OPEN') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]">
          <Play size={11} className="fill-[#159B55]" />
          <span>Active</span>
        </span>
      );
    }
    if (s === 'IN_REVIEW' || s === 'UNDER_REVIEW' || s === 'REVIEW') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]">
          <Clock size={12} />
          <span>In Review</span>
        </span>
      );
    }
    if (s === 'COMPLETED' || s === 'CLOSED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]">
          <CheckCircle2 size={12} />
          <span>Completed</span>
        </span>
      );
    }
    if (s === 'ESCALATED' || s === 'FLAGGED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#FDF2F2] text-[#DC4545] border border-[#FAD8D8]">
          <AlertCircle size={12} />
          <span>Escalated</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#F4F5FB] text-[#73758B] border border-[#E6E5F0]">
        <span>{status}</span>
      </span>
    );
  };

  // Render Final Assessment Badge
  const renderAssessmentBadge = (tier?: string) => {
    const t = (tier || '').toUpperCase();
    if (t === 'HIGH_RISK') {
      return (
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#FDF2F2] text-[#DC4545] border border-[#FAD8D8]">
          High Risk
        </span>
      );
    }
    if (t === 'SUSPICIOUS' || t === 'REQUIRES REVIEW' || t === 'REQUIRES_REVIEW') {
      return (
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]">
          Requires Review
        </span>
      );
    }
    if (t === 'LOW_RISK' || t === 'AUTHENTIC') {
      return (
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]">
          Low Risk
        </span>
      );
    }
    return (
      <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#F4F5FB] text-[#73758B] border border-[#E6E5F0]">
        Pending
      </span>
    );
  };

  // Render Priority Pill
  const renderPriorityBadge = (priority?: string) => {
    const p = (priority || 'ROUTINE').toUpperCase();
    if (p === 'URGENT') {
      return (
        <span className="inline-block px-3 py-0.5 rounded-full text-xs font-semibold bg-[#FDF2F2] text-[#DC4545] border border-[#FAD8D8]">
          Urgent
        </span>
      );
    }
    if (p === 'HIGH') {
      return (
        <span className="inline-block px-3 py-0.5 rounded-full text-xs font-semibold bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]">
          High
        </span>
      );
    }
    return (
      <span className="inline-block px-3 py-0.5 rounded-full text-xs font-semibold bg-[#F0EBFF] text-[#7045E8] border border-[#DDD5F9]">
        Routine
      </span>
    );
  };

  // Navigate to Case Details or Exhibit
  const handleViewCase = (item: InvestigationCase) => {
    if (item.primary_document_id) {
      navigate(`/investigation/${item.primary_document_id}`);
    } else {
      navigate('/new');
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* ------------------------------------------------------------- */}
      {/* SECTION 1: INVESTIGATION CASES PURPLE GRADIENT BANNER         */}
      {/* ------------------------------------------------------------- */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#211244] via-[#3B1F70] to-[#6035C8] p-7 text-white shadow-md">
        {/* Subtle decorative radial glow */}
        <div className="absolute -right-16 -top-16 w-64 h-64 rounded-full bg-[#7045E8]/25 blur-3xl pointer-events-none" />
        <div className="absolute right-1/3 -bottom-20 w-80 h-80 rounded-full bg-[#9065F8]/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          {/* Left: 3D Folder Illustration & Typography */}
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center p-3 shadow-inner shrink-0">
              <svg viewBox="0 0 64 64" fill="none" className="w-full h-full drop-shadow-md">
                <path d="M6 18C6 14.6863 8.68629 12 12 12H24L30 18H52C55.3137 18 58 20.6863 58 24V46C58 49.3137 55.3137 52 52 52H12C8.68629 52 6 49.3137 6 46V18Z" fill="#805AD5" fillOpacity="0.65"/>
                <path d="M12 24H52C55.3137 24 58 26.6863 58 30V48C58 51.3137 55.3137 54 52 54H12C8.68629 54 6 51.3137 6 48V30C6 26.6863 8.68629 24 12 24Z" fill="#B794F4" fillOpacity="0.9"/>
                <rect x="18" y="14" width="28" height="20" rx="3" fill="#FFFFFF" fillOpacity="0.95"/>
                <line x1="22" y1="20" x2="38" y2="20" stroke="#7045E8" strokeWidth="2" strokeLinecap="round"/>
                <line x1="22" y1="25" x2="34" y2="25" stroke="#7045E8" strokeWidth="2" strokeLinecap="round"/>
                <circle cx="48" cy="40" r="5" fill="#159B55" />
                <path d="M46 40L47.5 41.5L50 39" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-black text-white tracking-tight">
                Investigation Cases
              </h2>
              <p className="text-xs text-purple-200/90 mt-1 max-w-xl leading-relaxed">
                Track case progress, manage exhibits, and monitor final decisions.
              </p>
            </div>
          </div>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-3 w-full md:w-auto">
            <button
              onClick={() => setIsNewCaseModalOpen(true)}
              className="flex-1 md:flex-initial px-4 py-2.5 bg-white hover:bg-slate-100 text-[#17172F] font-bold text-xs rounded-xl shadow-sm flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
            >
              <Plus size={16} className="text-[#7045E8]" />
              <span>New Case</span>
            </button>
            <button
              onClick={handleExportCases}
              className="flex-1 md:flex-initial px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white border border-white/25 font-semibold text-xs rounded-xl flex items-center justify-center gap-2 transition-all backdrop-blur-sm active:scale-[0.98]"
            >
              <Download size={15} />
              <span>Export Case List</span>
            </button>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 2: 5 KPI SUMMARY CARDS                                */}
      {/* ------------------------------------------------------------- */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Card 1: Total Cases */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
              <Folder size={20} />
            </div>
            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#159B55] bg-[#EBF9F1] px-2 py-0.5 rounded-full">
              <TrendingUp size={11} /> +18%
            </span>
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Total Cases</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight">
                {stats.total_cases}
              </span>
              <span className="text-[10px] text-[#73758B]">vs. last 30 days</span>
            </div>
          </div>
        </div>

        {/* Card 2: Active Cases */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="w-10 h-10 rounded-xl bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center shrink-0">
            <Play size={18} className="fill-[#2563EB] ml-0.5" />
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Active Cases</span>
            <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight block mt-0.5">
              {stats.active}
            </span>
          </div>
        </div>

        {/* Card 3: Completed */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="w-10 h-10 rounded-xl bg-[#EBF9F1] text-[#159B55] flex items-center justify-center shrink-0">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Completed</span>
            <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight block mt-0.5">
              {stats.completed}
            </span>
          </div>
        </div>

        {/* Card 4: Under Review */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="w-10 h-10 rounded-xl bg-[#FFF8EC] text-[#E9A12A] flex items-center justify-center shrink-0">
            <Clock size={20} />
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Under Review</span>
            <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight block mt-0.5">
              {stats.under_review}
            </span>
          </div>
        </div>

        {/* Card 5: Escalated */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between col-span-2 md:col-span-1">
          <div className="w-10 h-10 rounded-xl bg-[#FDF2F2] text-[#DC4545] flex items-center justify-center shrink-0">
            <AlertCircle size={20} />
          </div>
          <div>
            <span className="text-xs text-[#73758B] font-medium block">Escalated</span>
            <span className="text-2xl md:text-3xl font-black text-[#17172F] tracking-tight block mt-0.5">
              {stats.escalated}
            </span>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 3: CASE MANAGEMENT TABLE CARD                         */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-sm p-6 space-y-5">
        {/* Filter Tabs and Search Bar */}
        <div className="flex flex-col lg:flex-row justify-between items-stretch lg:items-center gap-4">
          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0 scrollbar-none">
            {[
              { id: 'ALL', label: `All Cases (${stats.total_cases})` },
              { id: 'ACTIVE', label: `Active (${stats.active})` },
              { id: 'UNDER_REVIEW', label: `Under Review (${stats.under_review})` },
              { id: 'COMPLETED', label: `Completed (${stats.completed})` },
              { id: 'ESCALATED', label: `Escalated (${stats.escalated})` },
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
            <div className="relative flex-1 sm:w-80">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by case ID, title or exhibit..."
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

            {/* Filters Button with Dropdown */}
            <div className="relative" ref={filterMenuRef}>
              <button
                type="button"
                onClick={() => setIsFilterMenuOpen(!isFilterMenuOpen)}
                className={`px-3.5 py-2 border rounded-xl text-xs font-semibold flex items-center gap-2 shadow-xs transition-colors ${
                  priorityFilter !== 'ALL'
                    ? 'bg-[#F0EBFF] text-[#7045E8] border-[#DDD5F9]'
                    : 'bg-white text-[#17172F] border-[#E6E5F0] hover:bg-[#F8F9FF]'
                }`}
              >
                <Filter size={14} className={priorityFilter !== 'ALL' ? 'text-[#7045E8]' : 'text-[#73758B]'} />
                <span>Filters</span>
                {priorityFilter !== 'ALL' && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#7045E8]" />
                )}
              </button>

              {/* Filter Menu Dropdown */}
              {isFilterMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white border border-[#E6E5F0] rounded-2xl shadow-elevated p-3 z-30 space-y-2">
                  <div className="flex items-center justify-between pb-1.5 border-b border-[#E6E5F0]">
                    <span className="text-[11px] font-bold text-[#17172F] uppercase tracking-wider">Priority Filter</span>
                    {priorityFilter !== 'ALL' && (
                      <button
                        onClick={() => setPriorityFilter('ALL')}
                        className="text-[10px] text-[#7045E8] hover:underline"
                      >
                        Reset
                      </button>
                    )}
                  </div>
                  <div className="space-y-1">
                    {(['ALL', 'ROUTINE', 'URGENT', 'HIGH'] as const).map((p) => (
                      <button
                        key={p}
                        onClick={() => {
                          setPriorityFilter(p);
                          setIsFilterMenuOpen(false);
                        }}
                        className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                          priorityFilter === p
                            ? 'bg-[#F0EBFF] text-[#7045E8] font-bold'
                            : 'text-[#5A5D72] hover:bg-[#F8F9FF]'
                        }`}
                      >
                        {p === 'ALL' ? 'All Priorities' : p.charAt(0) + p.slice(1).toLowerCase()}
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
            <p className="text-xs font-semibold text-[#17172F]">Loading Investigation Cases...</p>
            <p className="text-[11px] text-[#73758B]">Retrieving case dockets from custody database</p>
          </div>
        ) : error ? (
          <div className="py-16 text-center space-y-3">
            <AlertCircle size={28} className="text-[#DC4545] mx-auto" />
            <p className="text-sm font-bold text-[#17172F]">Unable to load case records</p>
            <button
              onClick={fetchData}
              className="px-4 py-2 bg-[#7045E8] text-white text-xs font-semibold rounded-xl hover:bg-[#5F33DB] transition-all shadow-sm"
            >
              Retry
            </button>
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <Folder size={32} className="text-slate-300 mx-auto" />
            <p className="text-sm font-bold text-[#17172F]">No cases found matching filters</p>
            <p className="text-xs text-[#73758B]">Try selecting a different status tab or clearing the search query.</p>
            <button
              onClick={() => {
                setActiveTab('ALL');
                setSearchQuery('');
                setPriorityFilter('ALL');
              }}
              className="px-4 py-2 bg-white border border-[#E6E5F0] hover:bg-[#F8F9FF] text-[#17172F] text-xs font-semibold rounded-xl transition-all shadow-xs"
            >
              Clear All Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-6 px-6">
            <table className="w-full text-left text-xs min-w-[900px]">
              <thead className="bg-[#F8F9FF] border-y border-[#E6E5F0] text-[#73758B] uppercase text-[10px] font-bold tracking-wider">
                <tr>
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Case Title & Description</th>
                  <th className="py-3 px-3 text-center">Exhibits</th>
                  <th className="py-3 px-3">Priority</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Final Assessment</th>
                  <th className="py-3 px-4">Updated</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E6E5F0]">
                {paginatedCases.map((item) => {
                  const { date, time } = formatDateTime(item.updated_at || item.created_at);
                  const isMenuOpen = openActionId === item.id;

                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-[#F8F9FF] transition-colors group cursor-pointer"
                      onClick={() => handleViewCase(item)}
                    >
                      {/* 1. Case ID */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-lg bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
                            <Folder size={14} />
                          </div>
                          <span className="font-mono font-bold text-[#7045E8] text-xs group-hover:underline">
                            {item.case_number}
                          </span>
                        </div>
                      </td>

                      {/* 2. Case Title & Description */}
                      <td className="py-4 px-4 min-w-[240px]">
                        <p className="font-bold text-[#17172F] text-xs leading-snug">
                          {item.title}
                        </p>
                        <p className="text-[11px] text-[#73758B] mt-0.5 line-clamp-1 leading-snug">
                          {item.notes || 'Forensic examination docket'}
                        </p>
                      </td>

                      {/* 3. Exhibits Count */}
                      <td className="py-4 px-3 text-center whitespace-nowrap">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-[#E6E5F0] bg-white text-xs font-mono font-semibold text-[#17172F]">
                          <Files size={12} className="text-[#73758B]" />
                          <span>{item.document_count || 1}</span>
                        </span>
                      </td>

                      {/* 4. Priority */}
                      <td className="py-4 px-3 whitespace-nowrap">
                        {renderPriorityBadge(item.priority)}
                      </td>

                      {/* 5. Status */}
                      <td className="py-4 px-3 whitespace-nowrap">
                        {renderStatusBadge(item.status)}
                      </td>

                      {/* 6. Final Assessment */}
                      <td className="py-4 px-3 whitespace-nowrap">
                        {renderAssessmentBadge(item.final_assessment)}
                      </td>

                      {/* 7. Updated */}
                      <td className="py-4 px-4 whitespace-nowrap font-mono">
                        <span className="text-xs text-[#17172F] block font-medium">{date}</span>
                        <span className="text-[10px] text-[#73758B] block mt-0.5">{time}</span>
                      </td>

                      {/* 8. Actions */}
                      <td className="py-4 px-4 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <div className="inline-flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => handleViewCase(item)}
                            className="px-3.5 py-1.5 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-semibold transition-all inline-flex items-center gap-1.5 shadow-sm active:scale-[0.98]"
                          >
                            <span>View Case</span>
                            <ArrowRight size={13} />
                          </button>

                          {/* Context Menu Button */}
                          <div className="relative">
                            <button
                              type="button"
                              onClick={() => setOpenActionId(isMenuOpen ? null : item.id)}
                              className="p-1.5 text-[#73758B] hover:text-[#17172F] hover:bg-[#F0EBFF] rounded-lg transition-colors border border-transparent hover:border-[#DDD5F9]"
                              aria-label="More actions"
                            >
                              <MoreVertical size={15} />
                            </button>

                            {/* Dropdown Menu */}
                            {isMenuOpen && (
                              <div
                                ref={actionMenuRef}
                                className="absolute right-0 mt-1 w-44 bg-white border border-[#E6E5F0] rounded-xl shadow-elevated py-1 z-40 text-left divide-y divide-[#E6E5F0]"
                              >
                                <div className="py-1">
                                  <button
                                    onClick={() => {
                                      setOpenActionId(null);
                                      handleViewCase(item);
                                    }}
                                    className="w-full px-3 py-1.5 text-xs text-[#17172F] hover:bg-[#F8F9FF] flex items-center gap-2"
                                  >
                                    <ExternalLink size={13} className="text-[#7045E8]" />
                                    <span>Open Investigation</span>
                                  </button>
                                  <button
                                    onClick={() => {
                                      setOpenActionId(null);
                                      navigate('/comparison');
                                    }}
                                    className="w-full px-3 py-1.5 text-xs text-[#17172F] hover:bg-[#F8F9FF] flex items-center gap-2"
                                  >
                                    <FileCheck size={13} className="text-[#159B55]" />
                                    <span>Compare Exhibit</span>
                                  </button>
                                </div>
                                <div className="py-1">
                                  <button
                                    onClick={() => {
                                      setOpenActionId(null);
                                      handleExportCases();
                                    }}
                                    className="w-full px-3 py-1.5 text-xs text-[#17172F] hover:bg-[#F8F9FF] flex items-center gap-2"
                                  >
                                    <Download size={13} className="text-[#73758B]" />
                                    <span>Export Case Docket</span>
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

        {/* ------------------------------------------------------------- */}
        {/* SECTION 4: PAGINATION CONTROLS                                */}
        {/* ------------------------------------------------------------- */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-[#E6E5F0]">
          <span className="text-xs text-[#73758B] font-mono">
            Showing {totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1} – {Math.min(currentPage * pageSize, totalItems)} of {totalItems} cases
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

            {/* Page number buttons */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
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

            {totalPages > 5 && (
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

      {/* ------------------------------------------------------------- */}
      {/* SECTION 5: NEW CASE CREATION MODAL                            */}
      {/* ------------------------------------------------------------- */}
      {isNewCaseModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-elevated w-full max-w-lg overflow-hidden space-y-0">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-[#E6E5F0] flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
                  <Plus size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#17172F]">Create Investigation Case</h3>
                  <p className="text-[11px] text-[#73758B]">Open a new forensic docket for document exhibit intake</p>
                </div>
              </div>
              <button
                onClick={() => setIsNewCaseModalOpen(false)}
                className="text-[#73758B] hover:text-[#17172F] p-1 rounded-lg"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleCreateCase} className="p-6 space-y-4">
              {caseError && (
                <div className="p-3 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl text-xs text-[#DC4545] flex items-center gap-2">
                  <AlertCircle size={15} className="shrink-0" />
                  <span>{caseError}</span>
                </div>
              )}

              {/* Title Field */}
              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17172F] block">
                  Case Title <span className="text-[#DC4545]">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Identity Credential Verification - Passport PA21"
                  className="w-full px-3.5 py-2 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-xs"
                />
              </div>

              {/* Priority & Status Grid */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-[#17172F] block">Priority</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as any)}
                    className="w-full px-3 py-2 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] focus:outline-none focus:border-[#7045E8] shadow-xs"
                  >
                    <option value="ROUTINE">Routine</option>
                    <option value="URGENT">Urgent</option>
                    <option value="HIGH">High Priority</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-[#17172F] block">Initial Status</label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] focus:outline-none focus:border-[#7045E8] shadow-xs"
                  >
                    <option value="ACTIVE">Active</option>
                    <option value="IN_REVIEW">In Review</option>
                  </select>
                </div>
              </div>

              {/* Description / Notes */}
              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17172F] block">
                  Description / Investigation Notes
                </label>
                <textarea
                  rows={3}
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  placeholder="Specify case objectives, suspect tampering indicators, or intake notes..."
                  className="w-full px-3.5 py-2 bg-white border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-xs resize-none"
                />
              </div>

              {/* Form Footer */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#E6E5F0]">
                <button
                  type="button"
                  onClick={() => setIsNewCaseModalOpen(false)}
                  className="px-4 py-2 border border-[#E6E5F0] hover:bg-[#F8F9FF] text-[#17172F] rounded-xl text-xs font-semibold transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCase}
                  className="px-5 py-2 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
                >
                  {submittingCase ? <RefreshCw size={14} className="animate-spin" /> : <Plus size={15} />}
                  <span>Create Case</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
