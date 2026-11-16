import { useState, useRef, useEffect } from 'react';
import { Search, LogOut, Shield, ChevronDown, Menu } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

export default function Topbar({ navigationOpen, onToggleNavigation }: { navigationOpen: boolean; onToggleNavigation: () => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setDropdownOpen(false);
    };
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Overview';
      case '/new': return 'New investigation';
      case '/comparison': return 'Document comparison';
      case '/cases': return 'Case Management';
      case '/analytics': return 'Analytics';
      case '/reports': return 'Reports';
      case '/settings': return 'Settings';
      default:
        if (location.pathname.startsWith('/investigation/')) {
          return 'Investigation Exhibit Dashboard';
        }
        return 'VisionForensics AI';
    }
  };

  const getBreadcrumbs = () => {
    const title = getPageTitle();
    if (location.pathname.startsWith('/investigation/')) {
      const docId = location.pathname.split('/')[2];
      return `Cases / Exhibit ${docId.substring(0, 8)}...`;
    }
    return `Workspace / ${title}`;
  };

  const formatRole = (role?: string) => {
    switch (role) {
      case 'SYSTEM_ADMINISTRATOR':
        return 'System Administrator';
      case 'SENIOR_INVESTIGATOR':
        return 'Senior Investigator';
      case 'FORENSIC_ANALYST':
        return 'Forensic Analyst';
      default:
        return 'Examiner';
    }
  };

  return (
    <header className="app-topbar border-b border-ink-border flex items-center justify-between sticky top-0 z-20 shrink-0">
      <div className="flex items-center gap-3 min-w-0">
        <button type="button" className="navigation-toggle" onClick={onToggleNavigation} aria-label="Toggle navigation" aria-controls="workspace-navigation" aria-expanded={navigationOpen}><Menu size={21} /></button>
        <div className="min-w-0">
          <p className="text-xs text-muted truncate">{getBreadcrumbs()}</p>
          <p className="text-sm font-semibold text-gray-100 mt-1 truncate">{getPageTitle()}</p>
        </div>
      </div>

      <div className="flex items-center gap-5">
        {/* Search */}
        <button type="button" onClick={() => navigate('/cases')} className="workspace-search hidden md:flex items-center gap-3 text-xs text-muted"><Search size={16} /><span>Find a document</span><span className="text-gray-600">/</span></button>

        {/* User Profile Badge & Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            aria-expanded={dropdownOpen}
            aria-controls="profile-dropdown"
            aria-label="Account options"
            className="flex items-center gap-3 py-1.5 px-3 rounded-lg hover:bg-ink-hover border border-transparent hover:border-ink-border transition-colors text-left"
          >
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-brand/20 border border-brand/40 text-brand font-semibold text-xs shrink-0">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-semibold text-gray-200 leading-tight">
                {user?.full_name || 'Authenticated Analyst'}
              </p>
              <p className="text-[10px] text-brand font-medium">
                {formatRole(user?.role)}
              </p>
            </div>
            <ChevronDown size={14} className="text-gray-400" />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div id="profile-dropdown" className="absolute right-0 mt-2 w-64 bg-ink-panel border border-ink-border rounded-xl shadow-2xl z-50 overflow-hidden divide-y divide-ink-border">
              <div className="p-4 bg-ink-base/50">
                <p className="text-xs font-bold text-white truncate">{user?.full_name}</p>
                <p className="text-[11px] text-gray-400 truncate mt-0.5">{user?.email}</p>
                <div className="mt-2.5 inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-brand/15 text-brand border border-brand/30">
                  <Shield size={11} />
                  <span>{formatRole(user?.role)}</span>
                </div>
              </div>

              <div className="p-1.5">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-red-400 hover:text-red-300 hover:bg-severity-critical/10 rounded-lg transition-colors"
                >
                  <LogOut size={15} />
                  <span>Sign Out Session</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
