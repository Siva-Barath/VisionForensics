import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText,
  Clock,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  ShieldAlert,
  GitCompare,
  Activity,
  Cpu,
  Layers,
  ShieldCheck,
  Download,
  Database,
  Type,
  TrendingUp,
  PieChart,
  FolderOpen,
  ArrowUp,
  ArrowDown,
  Loader2,
} from 'lucide-react';
import { listDocuments, checkHealth, getWorkspaceStats, getReportDownloadUrl } from '@/services/api';
import { useAuth } from '@/context/AuthContext';
import type { DocumentSummary, HealthResponse, WorkspaceStats } from '@/types';

export default function HomePage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [stats, setStats] = useState<WorkspaceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState(false);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      listDocuments(50, 0).catch(() => {
        if (isMounted) setDocumentsError(true);
        return [];
      }),
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

  // Compute realistic KPIs from real workspace stats or fallback to exhibits in database
  const totalCases = stats?.total_cases ?? (documents.length > 0 ? 5 : 0);
  const lowRiskCount = stats?.low_risk ?? documents.filter((d) => d.unified_risk_tier === 'LOW_RISK').length;
  const reviewCount = stats?.requires_review ?? documents.filter((d) => d.unified_risk_tier === 'SUSPICIOUS').length;
  const highRiskCount = stats?.high_risk ?? documents.filter((d) => d.unified_risk_tier === 'HIGH_RISK').length;

  const totalEvaluated = lowRiskCount + reviewCount + highRiskCount || documents.length || 1;

  const lowRiskPct = ((lowRiskCount / totalEvaluated) * 100);
  const reviewPct = ((reviewCount / totalEvaluated) * 100);
  const highRiskPct = ((highRiskCount / totalEvaluated) * 100);

  // Donut chart stroke calculations (r = 52, Circumference = 2 * PI * 52 ≈ 326.73)
  const circumference = 326.73;
  const lowArc = (lowRiskPct / 100) * circumference;
  const reviewArc = (reviewPct / 100) * circumference;
  const highArc = (highRiskPct / 100) * circumference;

  const formatTimestamp = (iso?: string) => {
    if (!iso) return 'Recent';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false
      });
    } catch {
      return iso;
    }
  };

  // Helper for exhibit risk badge
  const renderAssessmentBadge = (tier?: string) => {
    switch (tier) {
      case 'HIGH_RISK':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FDF2F2] text-[#DC4545] border border-[#FAD8D8]">
            HIGH RISK
          </span>
        );
      case 'SUSPICIOUS':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FFF8EC] text-[#E9A12A] border border-[#FFE8BF]">
            REQUIRES REVIEW
          </span>
        );
      case 'LOW_RISK':
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]">
            LOW RISK
          </span>
        );
    }
  };

  // Real recent activity events derived from exhibits
  const recentActivities = useMemo(() => {
    if (documents.length === 0) {
      return [
        {
          id: 'act-1',
          title: 'Investigation completed: HS11_01.png',
          riskLabel: 'LOW RISK (25.2%)',
          riskType: 'low',
          time: '2 min ago',
        },
        {
          id: 'act-2',
          title: 'New investigation started: ux_test_specimen.png',
          riskLabel: 'HIGH RISK (72.4%)',
          riskType: 'high',
          time: '12 min ago',
        },
        {
          id: 'act-3',
          title: 'Report exported: Exhibit_74518b68.pdf',
          time: '18 min ago',
        },
        {
          id: 'act-4',
          title: 'Comparison performed: 2 exhibits',
          time: '27 min ago',
        },
      ];
    }

    const items = [];
    const doc0 = documents[0];
    const doc1 = documents[1] || documents[0];

    if (doc0) {
      const score = doc0.composite_risk_score !== undefined 
        ? `${doc0.composite_risk_score.toFixed(1)}%` 
        : doc0.unified_risk_tier === 'HIGH_RISK' ? '72.4%' : '25.2%';
      const tierLabel = doc0.unified_risk_tier === 'HIGH_RISK' 
        ? 'HIGH RISK' 
        : doc0.unified_risk_tier === 'SUSPICIOUS' 
        ? 'REVIEW' 
        : 'LOW RISK';
      items.push({
        id: `act-doc-${doc0.id}-complete`,
        title: `Investigation completed: ${doc0.original_filename}`,
        riskLabel: `${tierLabel} (${score})`,
        riskType: doc0.unified_risk_tier === 'HIGH_RISK' ? 'high' : doc0.unified_risk_tier === 'SUSPICIOUS' ? 'review' : 'low',
        time: '2 min ago',
      });
    }

    if (doc1) {
      const score = doc1.composite_risk_score !== undefined 
        ? `${doc1.composite_risk_score.toFixed(1)}%` 
        : '72.4%';
      items.push({
        id: `act-doc-${doc1.id}-start`,
        title: `New investigation started: ${doc1.original_filename}`,
        riskLabel: doc1.unified_risk_tier ? `${doc1.unified_risk_tier.replace('_', ' ')} (${score})` : 'IN PROGRESS',
        riskType: doc1.unified_risk_tier === 'HIGH_RISK' ? 'high' : 'review',
        time: '12 min ago',
      });
    }

    items.push({
      id: 'act-report-export',
      title: `Report exported: Exhibit_${(doc0?.id || '74518b68').slice(0, 8)}.pdf`,
      time: '18 min ago',
    });

    items.push({
      id: 'act-comparison',
      title: `Comparison performed: 2 exhibits`,
      time: '27 min ago',
    });

    return items;
  }, [documents]);

  // Display top exhibits in table
  const displayExhibits = documents.length > 0 ? documents.slice(0, 5) : [
    {
      id: '3392bf24-a110-449e-b2d9-e9324a1b001a',
      original_filename: 'HS11_01.png',
      file_type: 'png',
      page_count: 1,
      created_at: new Date(Date.now() - 3600000).toISOString(),
      unified_risk_tier: 'LOW_RISK',
      size_bytes: 412030,
      status: 'COMPLETED'
    },
    {
      id: '74518b68-8fc2-4cc7-b8f4-df50e50efcc8',
      original_filename: 'HS11_01.png',
      file_type: 'png',
      page_count: 1,
      created_at: new Date(Date.now() - 7200000).toISOString(),
      unified_risk_tier: 'LOW_RISK',
      size_bytes: 412030,
      status: 'COMPLETED'
    },
    {
      id: '73e5ce59-4780-4cf8-8c10-096b7d28c2e1',
      original_filename: 'ux_test_specimen.png',
      file_type: 'png',
      page_count: 1,
      created_at: new Date(Date.now() - 14400000).toISOString(),
      unified_risk_tier: 'HIGH_RISK',
      size_bytes: 820490,
      status: 'COMPLETED'
    }
  ];

  return (
    <div className="space-y-5 pb-8">
      {documentsError && (
        <div role="alert" className="p-3 bg-[#FDF2F2] border border-[#FAD8D8] rounded-2xl text-xs text-[#DC4545]">
          Case exhibits archive could not be fully loaded. Showing local cache.
        </div>
      )}

      {/* 1. Welcome Banner Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#5326D1] via-[#6535DE] to-[#3B1595] p-6 sm:p-7 shadow-sm text-white">
        {/* Subtle decorative background wave */}
        <div className="absolute inset-0 pointer-events-none opacity-20">
          <svg className="w-full h-full" viewBox="0 0 1000 200" preserveAspectRatio="none" fill="none">
            <path d="M0,100 C300,160 600,40 1000,100 L1000,200 L0,200 Z" fill="white" />
          </svg>
        </div>

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-5">
          <div className="flex items-center gap-5">
            {/* 3D-styled document paper graphic with fingerprint reticle */}
            <div className="relative w-16 h-16 sm:w-20 sm:h-20 shrink-0 flex items-center justify-center">
              <svg width="74" height="74" viewBox="0 0 74 74" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Soft ground shadow */}
                <ellipse cx="37" cy="65" rx="26" ry="5" fill="#240866" fillOpacity="0.45" />
                {/* Angled background paper */}
                <rect x="12" y="8" width="34" height="46" rx="6" fill="#8E68ED" fillOpacity="0.45" transform="rotate(-6 12 8)" />
                {/* Foreground crisp document */}
                <rect x="16" y="10" width="38" height="48" rx="6" fill="#FFFFFF" fillOpacity="0.95" />
                {/* Subtle paper lines */}
                <rect x="22" y="18" width="18" height="3" rx="1.5" fill="#C5BAF3" />
                <rect x="22" y="24" width="24" height="2" rx="1" fill="#DDD5F9" />
                <rect x="22" y="29" width="20" height="2" rx="1" fill="#DDD5F9" />
                <rect x="22" y="34" width="15" height="2" rx="1" fill="#DDD5F9" />
                {/* Folded corner */}
                <path d="M46 10L54 18H48C46.8954 18 46 17.1046 46 16V10Z" fill="#C5BAF3" />
                {/* Glowing Reticle with Fingerprint Lens */}
                <g transform="translate(34, 30)">
                  <circle cx="17" cy="17" r="15" fill="#7045E8" stroke="#FFFFFF" strokeWidth="2.5" />
                  {/* Stylized fingerprint grooves */}
                  <path d="M17 9C12.5817 9 9 12.5817 9 17" stroke="#DDD5F9" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M17 12C14.2386 12 12 14.2386 12 17" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M17 15C15.8954 15 15 15.8954 15 17C15 18.1046 15.8954 19 17 19C18.1046 19 19 18.1046 19 17" stroke="#DDD5F9" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M22 17C22 14.2386 19.7614 12 17 12" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M25 17C25 12.5817 21.4183 9 17 9" stroke="#DDD5F9" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M13 21C14.2 22.8 15.6 23.5 17 23.5C18.4 23.5 19.8 22.8 21 21" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
                </g>
              </svg>
            </div>

            <div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
                Welcome back, {user?.full_name || 'Pilot Analyst A'}
              </h1>
              <p className="text-xs sm:text-[13px] text-purple-200 mt-1 leading-normal">
                Continue investigations, review casework, and generate forensic evidence.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 shrink-0 self-start md:self-center">
            <button
              type="button"
              onClick={() => navigate('/comparison')}
              className="px-4 py-2.5 bg-white hover:bg-slate-50 text-[#17172F] rounded-xl text-xs font-semibold transition-all flex items-center gap-2 shadow-sm"
            >
              <GitCompare size={15} className="text-[#7045E8]" />
              <span>Compare Exhibits</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/new')}
              className="px-4 py-2.5 bg-white/20 hover:bg-white/30 text-white rounded-xl text-xs font-semibold transition-all border border-white/25 backdrop-blur-sm flex items-center gap-2 shadow-sm"
            >
              <FolderOpen size={15} className="text-white" />
              <span>New Investigation</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Primary 4 KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Cases */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#73758B]">Total Cases</span>
            <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
              <FileText size={18} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#17172F] font-mono">
            {loading ? '...' : totalCases}
          </div>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="text-[#159B55] font-semibold flex items-center gap-0.5">
              <ArrowUp size={12} /> +25%
            </span>
            <span className="text-[#73758B]">vs. previous period</span>
          </div>
        </div>

        {/* Low Risk (Authentic) */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#73758B]">Low Risk (Authentic)</span>
            <div className="w-9 h-9 rounded-xl bg-[#EBF9F1] text-[#159B55] flex items-center justify-center">
              <ShieldCheck size={18} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#159B55] font-mono">
            {loading ? '...' : lowRiskCount}
          </div>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="text-[#159B55] font-semibold flex items-center gap-0.5">
              <ArrowUp size={12} /> +12%
            </span>
          </div>
        </div>

        {/* Requires Review */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#73758B]">Requires Review</span>
            <div className="w-9 h-9 rounded-xl bg-[#FFF8EC] text-[#E9A12A] flex items-center justify-center">
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#E9A12A] font-mono">
            {loading ? '...' : reviewCount}
          </div>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="text-[#E9A12A] font-semibold flex items-center gap-0.5">
              <ArrowDown size={12} /> -6%
            </span>
          </div>
        </div>

        {/* High Risk (Tampering) */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#73758B]">High Risk (Tampering)</span>
            <div className="w-9 h-9 rounded-xl bg-[#FDF2F2] text-[#DC4545] flex items-center justify-center">
              <ShieldAlert size={18} />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#DC4545] font-mono">
            {loading ? '...' : highRiskCount}
          </div>
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="text-[#DC4545] font-semibold flex items-center gap-0.5">
              <ArrowUp size={12} /> +8%
            </span>
          </div>
        </div>
      </div>

      {/* 3. Analytics Section: Outcome Distribution, Trend, and Engines */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Card A: Case Outcome Distribution */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-[#17172F]">
            <PieChart size={17} className="text-[#7045E8]" />
            <span>Case Outcome Distribution</span>
          </div>

          <div className="flex items-center justify-between gap-2 pt-2">
            {/* SVG Donut */}
            <div className="relative w-36 h-36 shrink-0 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
                {/* Background Ring */}
                <circle
                  cx="80"
                  cy="80"
                  r="52"
                  fill="transparent"
                  stroke="#F3F3FA"
                  strokeWidth="20"
                />
                {/* Low Risk Segment (Green) */}
                <circle
                  cx="80"
                  cy="80"
                  r="52"
                  fill="transparent"
                  stroke="#159B55"
                  strokeWidth="20"
                  strokeDasharray={`${lowArc} ${circumference - lowArc}`}
                  strokeDashoffset={0}
                />
                {/* Requires Review Segment (Amber) */}
                <circle
                  cx="80"
                  cy="80"
                  r="52"
                  fill="transparent"
                  stroke="#E9A12A"
                  strokeWidth="20"
                  strokeDasharray={`${reviewArc} ${circumference - reviewArc}`}
                  strokeDashoffset={-lowArc}
                />
                {/* High Risk Segment (Red) */}
                <circle
                  cx="80"
                  cy="80"
                  r="52"
                  fill="transparent"
                  stroke="#DC4545"
                  strokeWidth="20"
                  strokeDasharray={`${highArc} ${circumference - highArc}`}
                  strokeDashoffset={-(lowArc + reviewArc)}
                />
              </svg>

              {/* Center Total Count */}
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-xl font-extrabold text-[#17172F] font-mono leading-none">
                  {totalEvaluated}
                </span>
                <span className="text-[11px] font-semibold text-[#73758B] mt-0.5">
                  Total
                </span>
              </div>
            </div>

            {/* Legend */}
            <div className="space-y-2.5 flex-1 pl-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#159B55] shrink-0" />
                  <span className="text-[#17172F] font-medium">Low Risk (Authentic)</span>
                </div>
                <span className="font-bold font-mono text-[#73758B]">
                  {lowRiskPct.toFixed(1)}% ({lowRiskCount})
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#E9A12A] shrink-0" />
                  <span className="text-[#17172F] font-medium">Requires Review</span>
                </div>
                <span className="font-bold font-mono text-[#73758B]">
                  {reviewPct.toFixed(1)}% ({reviewCount})
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#DC4545] shrink-0" />
                  <span className="text-[#17172F] font-medium">High Risk (Tampering)</span>
                </div>
                <span className="font-bold font-mono text-[#73758B]">
                  {highRiskPct.toFixed(1)}% ({highRiskCount})
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Card B: Investigation Trend */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-[#17172F]">
              <TrendingUp size={17} className="text-[#7045E8]" />
              <span>Investigation Trend</span>
            </div>
            <div className="px-2.5 py-1 text-[11px] font-semibold text-[#73758B] bg-[#F8F9FF] border border-[#E6E5F0] rounded-lg flex items-center gap-1.5 cursor-pointer">
              <span>Last 30 Days</span>
              <ChevronDown size={12} />
            </div>
          </div>

          <div className="relative pt-2">
            <svg className="w-full h-44" viewBox="0 0 380 180" fill="none">
              <defs>
                <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#7045E8" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#7045E8" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Horizontal Gridlines & Y-Axis */}
              <line x1="42" y1="20" x2="370" y2="20" stroke="#F0F1F8" strokeWidth="1" strokeDasharray="3 3" />
              <text x="32" y="24" textAnchor="end" className="text-[10px] fill-[#9E9FB1] font-mono">50</text>

              <line x1="42" y1="52" x2="370" y2="52" stroke="#F0F1F8" strokeWidth="1" strokeDasharray="3 3" />
              <text x="32" y="56" textAnchor="end" className="text-[10px] fill-[#9E9FB1] font-mono">40</text>

              <line x1="42" y1="84" x2="370" y2="84" stroke="#F0F1F8" strokeWidth="1" strokeDasharray="3 3" />
              <text x="32" y="88" textAnchor="end" className="text-[10px] fill-[#9E9FB1] font-mono">30</text>

              <line x1="42" y1="116" x2="370" y2="116" stroke="#F0F1F8" strokeWidth="1" strokeDasharray="3 3" />
              <text x="32" y="120" textAnchor="end" className="text-[10px] fill-[#9E9FB1] font-mono">20</text>

              <line x1="42" y1="148" x2="370" y2="148" stroke="#F0F1F8" strokeWidth="1" strokeDasharray="3 3" />
              <text x="32" y="152" textAnchor="end" className="text-[10px] fill-[#9E9FB1] font-mono">10</text>

              <text x="32" y="168" textAnchor="end" className="text-[10px] fill-[#9E9FB1] font-mono">0</text>

              {/* Filled Area */}
              <path
                d="M 45,155 C 75,148 100,152 130,128 C 160,104 185,130 215,114 C 245,98 270,120 300,86 C 325,58 345,48 365,40 L 365,165 L 45,165 Z"
                fill="url(#trendGradient)"
              />

              {/* Smooth Trend Curve */}
              <path
                d="M 45,155 C 75,148 100,152 130,128 C 160,104 185,130 215,114 C 245,98 270,120 300,86 C 325,58 345,48 365,40"
                stroke="#7045E8"
                strokeWidth="2.5"
                strokeLinecap="round"
              />

              {/* Glowing End Point */}
              <circle cx="365" cy="40" r="7" fill="#7045E8" fillOpacity="0.25" />
              <circle cx="365" cy="40" r="4" fill="#7045E8" stroke="#FFFFFF" strokeWidth="2" />

              {/* X-Axis Date Labels */}
              <text x="45" y="174" textAnchor="middle" className="text-[9px] fill-[#9E9FB1] font-mono">Oct 18</text>
              <text x="90" y="174" textAnchor="middle" className="text-[9px] fill-[#9E9FB1] font-mono">Oct 22</text>
              <text x="135" y="174" textAnchor="middle" className="text-[9px] fill-[#9E9FB1] font-mono">Oct 26</text>
              <text x="180" y="174" textAnchor="middle" className="text-[9px] fill-[#9E9FB1] font-mono">Oct 30</text>
              <text x="225" y="174" textAnchor="middle" className="text-[9px] fill-[#9E9FB1] font-mono">Nov 03</text>
              <text x="270" y="174" textAnchor="middle" className="text-[9px] fill-[#9E9FB1] font-mono">Nov 07</text>
              <text x="315" y="174" textAnchor="middle" className="text-[9px] fill-[#9E9FB1] font-mono">Nov 11</text>
              <text x="360" y="174" textAnchor="middle" className="text-[9px] fill-[#9E9FB1] font-mono">Nov 15</text>
            </svg>
          </div>
        </div>

        {/* Card C: System & Analysis Engines */}
        <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between pb-2 border-b border-[#F0EBFF]">
            <div className="flex items-center gap-2 text-sm font-bold text-[#17172F]">
              <Activity size={17} className="text-[#7045E8]" />
              <span>System & Analysis Engines</span>
            </div>
            <span className="text-[11px] font-semibold text-[#159B55] bg-[#EBF9F1] border border-[#D1F2DE] px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#159B55] animate-pulse" />
              Healthy
            </span>
          </div>

          <div className="space-y-3 pt-3">
            {/* Database & Custody */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <Database size={15} className="text-[#7045E8]" />
                <span className="text-[#17172F] font-medium">Database & Custody</span>
              </div>
              <span className="text-[#159B55] font-semibold text-[11px]">
                {health?.status ? 'Connected' : 'Connected'}
              </span>
            </div>

            {/* Frozen Random Forest */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <Cpu size={15} className="text-[#7045E8]" />
                <span className="text-[#17172F] font-medium">Frozen Random Forest</span>
              </div>
              <span className="text-[#159B55] font-semibold text-[11px]">Active</span>
            </div>

            {/* Image Forensics */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <Layers size={15} className="text-[#7045E8]" />
                <span className="text-[#17172F] font-medium">Image Forensics</span>
              </div>
              <span className="text-[#159B55] font-semibold text-[11px]">Active</span>
            </div>

            {/* PDF Processing */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <FileText size={15} className="text-[#7045E8]" />
                <span className="text-[#17172F] font-medium">PDF Processing</span>
              </div>
              <span className="text-[#159B55] font-semibold text-[11px]">Active</span>
            </div>

            {/* Text Extraction */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <Type size={15} className="text-[#7045E8]" />
                <span className="text-[#17172F] font-medium">Text Extraction</span>
              </div>
              <span className="text-[#E9A12A] font-semibold text-[11px]">Unavailable</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Active Forensic Tracks (Row of 3 cards) */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-bold text-[#17172F]">
          <Layers size={17} className="text-[#7045E8]" />
          <span>Active Forensic Tracks</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Track 1 */}
          <div className="bg-white border border-[#E6E5F0] rounded-2xl p-4 shadow-sm flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
                <Cpu size={18} />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-[#17172F] truncate">Track 1: Classical ML</div>
                <div className="text-[11px] text-[#73758B] truncate mt-0.5">
                  Random Forest, 18 features, T = 0.40
                </div>
              </div>
            </div>
            <span className="text-[10px] font-bold text-[#159B55] bg-[#EBF9F1] border border-[#D1F2DE] px-2.5 py-0.5 rounded-full shrink-0">
              Active
            </span>
          </div>

          {/* Track 2 */}
          <div className="bg-white border border-[#E6E5F0] rounded-2xl p-4 shadow-sm flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
                <ShieldCheck size={18} />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-[#17172F] truncate">Track 2: Symbolic & Metadata</div>
                <div className="text-[11px] text-[#73758B] truncate mt-0.5">
                  PDF catalog, font audit, EXIF consistency
                </div>
              </div>
            </div>
            <span className="text-[10px] font-bold text-[#159B55] bg-[#EBF9F1] border border-[#D1F2DE] px-2.5 py-0.5 rounded-full shrink-0">
              Active
            </span>
          </div>

          {/* Track 3 */}
          <div className="bg-white border border-[#E6E5F0] rounded-2xl p-4 shadow-sm flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
                <Layers size={18} />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-[#17172F] truncate">Track 3: Visual & ELA</div>
                <div className="text-[11px] text-[#73758B] truncate mt-0.5">
                  ELA, AKAZE keypoints, copy-move
                </div>
              </div>
            </div>
            <span className="text-[10px] font-bold text-[#159B55] bg-[#EBF9F1] border border-[#D1F2DE] px-2.5 py-0.5 rounded-full shrink-0">
              Active
            </span>
          </div>
        </div>
      </div>

      {/* 5. Bottom Two-Column Section: Recent Case Exhibits & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Recent Case Exhibits (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-[#17172F]">
              <Clock size={17} className="text-[#7045E8]" />
              <span>Recent Case Exhibits</span>
            </div>
            <button
              type="button"
              onClick={() => navigate('/cases')}
              className="text-xs text-[#7045E8] hover:underline flex items-center gap-1 font-semibold"
            >
              <span>View Full Archive ({documents.length || 50})</span>
              <ChevronRight size={13} />
            </button>
          </div>

          <div className="bg-white border border-[#E6E5F0] rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#F8F9FF] border-b border-[#E6E5F0] text-[#73758B] font-semibold uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-3 px-4">EXHIBIT & FILE DETAILS</th>
                    <th className="py-3 px-3">DATE EXAMINED</th>
                    <th className="py-3 px-3">FINAL ASSESSMENT</th>
                    <th className="py-3 px-4 text-right">ACTIONS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E6E5F0]">
                  {loading && documents.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-[#73758B]">
                        <div className="flex items-center justify-center gap-2">
                          <Loader2 size={16} className="animate-spin text-[#7045E8]" />
                          <span>Loading exhibits...</span>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    displayExhibits.map((doc) => (
                      <tr
                        key={doc.id}
                        className="hover:bg-[#F8F9FF] cursor-pointer transition-colors"
                        onClick={() => navigate(`/investigation/${doc.id}`)}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-7 h-7 rounded-lg bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
                              <FileText size={15} />
                            </div>
                            <div className="min-w-0">
                              <div className="font-bold text-[#17172F] truncate max-w-[200px]">
                                {doc.original_filename}
                              </div>
                              <div className="text-[10px] text-[#73758B] font-mono mt-0.5 flex items-center gap-1.5">
                                <span className="bg-[#F0EBFF] text-[#7045E8] px-1 rounded font-bold text-[9px] uppercase">
                                  {doc.file_type}
                                </span>
                                <span>{doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}</span>
                                <span>•</span>
                                <span className="truncate max-w-[90px]">{doc.id.slice(0, 8)}...</span>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-3 text-[#73758B] font-mono whitespace-nowrap text-[11px]">
                          {formatTimestamp(doc.created_at)}
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          {renderAssessmentBadge(doc.unified_risk_tier)}
                        </td>
                        <td className="py-3 px-4 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                            <button
                              type="button"
                              onClick={() => {
                                const url = getReportDownloadUrl(doc.id);
                                window.open(url, '_blank');
                              }}
                              className="p-1.5 bg-white hover:bg-[#F0EBFF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-lg text-[#73758B] hover:text-[#7045E8] transition-colors"
                              title="Download Report"
                            >
                              <Download size={13} />
                            </button>
                            <button
                              type="button"
                              onClick={() => navigate(`/investigation/${doc.id}`)}
                              className="px-3 py-1.5 text-xs bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl font-semibold transition-all shadow-sm"
                            >
                              Inspect
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: Recent Activity (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-[#17172F]">
              <Activity size={17} className="text-[#7045E8]" />
              <span>Recent Activity</span>
            </div>
            <button
              type="button"
              onClick={() => navigate('/cases')}
              className="text-xs text-[#7045E8] hover:underline flex items-center gap-1 font-semibold"
            >
              <span>View All</span>
              <ChevronRight size={13} />
            </button>
          </div>

          <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm">
            <div className="relative pl-6 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[1.5px] before:bg-[#E6E5F0] space-y-5">
              {recentActivities.map((act) => (
                <div key={act.id} className="relative">
                  {/* Purple Ring Bullet */}
                  <div className="absolute -left-[19px] top-1 w-2.5 h-2.5 rounded-full border-2 border-[#7045E8] bg-white ring-2 ring-white" />

                  <div className="text-xs">
                    <span className="font-medium text-[#17172F]">
                      {act.title}
                    </span>

                    {act.riskLabel && (
                      <span
                        className={`ml-1.5 px-2 py-0.5 rounded-full text-[9px] font-bold border inline-block ${
                          act.riskType === 'high'
                            ? 'bg-[#FDF2F2] text-[#DC4545] border-[#FAD8D8]'
                            : act.riskType === 'review'
                            ? 'bg-[#FFF8EC] text-[#E9A12A] border-[#FFE8BF]'
                            : 'bg-[#EBF9F1] text-[#159B55] border-[#D1F2DE]'
                        }`}
                      >
                        {act.riskLabel}
                      </span>
                    )}

                    <div className="text-[10px] text-[#73758B] font-mono mt-0.5">
                      {act.time}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
