import { useState, useRef, useEffect } from 'react';
import { LogOut, Shield, ChevronDown, Menu, Bell } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

export default function Topbar({ 
  navigationOpen, 
  onToggleNavigation 
}: { 
  navigationOpen: boolean; 
  onToggleNavigation: () => void; 
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click or escape
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
      case '/': return 'Investigation Dashboard';
      case '/new': return 'New Document Investigation';
      case '/comparison': return 'Document Comparison & Differential Analysis';
      case '/cases': return 'Case Management';
      case '/analytics': return 'Caseload & Scientific Analytics';
      case '/reports': return 'Investigation Reports Archive';
      case '/settings': return 'System Settings & Governance';
      default:
        if (location.pathname.startsWith('/investigation/')) {
          return 'Investigation Result';
        }
        return 'VisionForensics AI';
    }
  };

  const getBreadcrumbs = () => {
    if (location.pathname.startsWith('/investigation/')) {
      const docId = location.pathname.split('/')[2];
      return `Cases > Exhibit ${docId.substring(0, 8)}...`;
    }
    switch (location.pathname) {
      case '/': return 'Workspace > Home';
      case '/new': return 'Workspace > New Investigation';
      case '/comparison': return 'Workspace > Differential Analysis';
      case '/cases': return 'Workspace > Cases';
      case '/analytics': return 'Workspace > Analytics';
      case '/reports': return 'Workspace > Reports Archive';
      case '/settings': return 'Workspace > Settings';
      default: return 'Workspace > VisionForensics AI';
    }
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
        return 'Forensic Analyst';
    }
  };

  return (
    <header className="app-topbar bg-white border-b border-[#E6E5F0] flex items-center justify-between sticky top-0 z-30 shrink-0 px-8 py-3.5 shadow-sm">
      {/* Left: Breadcrumbs & Page Title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          type="button"
          className="navigation-toggle lg:hidden p-1.5 text-slate-500 hover:text-navy"
          onClick={onToggleNavigation}
          aria-label="Toggle navigation"
          aria-expanded={navigationOpen}
        >
          <Menu size={22} />
        </button>
        <div className="min-w-0">
          <p className="text-xs font-medium text-[#73758B] tracking-wide truncate">
            {getBreadcrumbs()}
          </p>
          <h1 className="text-xl font-bold text-[#17172F] tracking-tight mt-0.5 truncate">
            {getPageTitle()}
          </h1>
          {location.pathname === '/' && (
            <p className="text-xs text-[#73758B] mt-0.5 hidden sm:block">
              Monitor investigations, analyze results, and manage forensic workflows.
            </p>
          )}
          {location.pathname === '/comparison' && (
            <p className="text-xs text-[#73758B] mt-0.5 hidden sm:block">
              Visually compare two document exhibits, quantify similarities, and highlight differences with forensic insights.
            </p>
          )}
          {location.pathname === '/cases' && (
            <p className="text-xs text-[#73758B] mt-0.5 hidden sm:block">
              Organize, track, and manage investigation cases from intake to closure.
            </p>
          )}
          {location.pathname === '/reports' && (
            <p className="text-xs text-[#73758B] mt-0.5 hidden sm:block">
              Access, review, and download finalized forensic investigation reports.
            </p>
          )}
          {location.pathname === '/settings' && (
            <p className="text-xs text-[#73758B] mt-0.5 hidden sm:block">
              Configure system parameters, monitor forensic engines and maintain evidentiary integrity.
            </p>
          )}
        </div>
      </div>

      {/* Right: Notifications & User Profile */}
      <div className="flex items-center gap-5">
        {/* Notification Bell */}
        <button
          type="button"
          className="relative p-2 rounded-xl text-[#73758B] hover:text-[#17172F] hover:bg-[#F0EBFF] transition-colors"
          title="Notifications"
          aria-label="Notifications"
        >
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#7045E8] ring-2 ring-white" />
        </button>

        {/* User Profile Badge & Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            aria-expanded={dropdownOpen}
            aria-controls="profile-dropdown"
            aria-label="Account options"
            className="flex items-center gap-3 py-1.5 px-2 rounded-xl hover:bg-[#F8F9FF] border border-transparent hover:border-[#E6E5F0] transition-colors text-left"
          >
            <div className="flex items-center justify-center w-9 h-9 rounded-full bg-[#7045E8] text-white font-bold text-sm shrink-0 shadow-sm">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'P'}
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-bold text-[#17172F] leading-tight">
                {user?.full_name || 'Pilot Analyst A'}
              </p>
              <p className="text-[11px] text-[#73758B] leading-tight mt-0.5">
                {formatRole(user?.role)}
              </p>
            </div>
            <ChevronDown size={14} className="text-[#73758B] ml-0.5" />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div
              id="profile-dropdown"
              className="absolute right-0 mt-2 w-64 bg-white border border-[#E6E5F0] rounded-2xl shadow-elevated z-50 overflow-hidden divide-y divide-[#E6E5F0]"
            >
              <div className="p-4 bg-[#F8F9FF]">
                <p className="text-xs font-bold text-[#17172F] truncate">
                  {user?.full_name || 'Pilot Analyst A'}
                </p>
                <p className="text-[11px] text-[#73758B] truncate mt-0.5">
                  {user?.email || 'analyst@pilot.visionforensics.local'}
                </p>
                <div className="mt-2.5 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#F0EBFF] text-[#7045E8] border border-[#DDD5F9]">
                  <Shield size={11} />
                  <span>{formatRole(user?.role)}</span>
                </div>
              </div>

              <div className="p-2 space-y-1">
                <button
                  type="button"
                  onClick={() => {
                    setDropdownOpen(false);
                    navigate('/settings');
                  }}
                  className="w-full text-left px-3 py-2 text-xs font-semibold text-[#17172F] hover:bg-[#F0EBFF] hover:text-[#7045E8] rounded-lg transition-colors"
                >
                  System Settings & Governance
                </button>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-[#DC4545] hover:bg-[#FDF2F2] rounded-lg transition-colors"
                >
                  <LogOut size={14} />
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
