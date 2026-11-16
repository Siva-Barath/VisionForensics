import { NavLink, useNavigate } from 'react-router-dom';
import {
  Home,
  PlusCircle,
  FolderOpen,
  BarChart2,
  FileText,
  Settings,
  ShieldCheck,
  User,
  X,
  GitCompare,
  LogOut,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const navItems = [
  { to: '/', label: 'Home', icon: Home, end: true },
  { to: '/new', label: 'New Investigation', icon: PlusCircle },
  { to: '/comparison', label: 'Comparison', icon: GitCompare },
  { to: '/cases', label: 'Cases', icon: FolderOpen },
  { to: '/analytics', label: 'Analytics', icon: BarChart2 },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const formatRole = (role?: string) => {
    switch (role) {
      case 'SYSTEM_ADMINISTRATOR':
        return 'System Admin';
      case 'SENIOR_INVESTIGATOR':
        return 'Sr. Investigator';
      case 'FORENSIC_ANALYST':
        return 'Forensic Analyst';
      default:
        return 'Analyst';
    }
  };

  return (
    <aside id="workspace-navigation" className={`app-sidebar flex flex-col bg-ink-panel border-r border-ink-border shrink-0 ${open ? 'is-open' : ''}`}>
      {/* Logo */}
      <div className="sidebar-brand flex items-center gap-3 px-6 py-6">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-brand/20 border border-brand shadow-inner shadow-brand/20">
          <ShieldCheck size={22} className="text-brand" />
        </div>
        <div>
          <p className="text-[15px] font-bold text-white tracking-tight">VisionForensics<span className="text-brand">.</span></p>
          <p className="text-[10px] text-muted uppercase tracking-widest font-medium mt-1">Document intelligence</p>
        </div>
        <button type="button" className="navigation-close" onClick={onClose} aria-label="Close navigation"><X size={18} /></button>
      </div>

      {/* Navigation */}
      <nav aria-label="Main navigation" className="flex-1 px-4 py-6 space-y-1">
        <p className="nav-section-label">Workspace</p>
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `nav-item flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'is-active bg-brand/10 text-brand'
                  : 'text-gray-400 hover:bg-ink-hover hover:text-gray-100'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-ink-border flex flex-col gap-4">
        <div className="sidebar-note">
          <ShieldCheck size={17} className="text-brand shrink-0" />
          <div><p className="text-xs font-medium text-gray-200">Evidence matters.</p><p className="text-[11px] text-muted mt-1 leading-relaxed">Examine with clarity. Investigate with confidence.</p></div>
        </div>

        <div className="flex items-center justify-between mt-1">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-brand/20 border border-brand/40 text-brand font-semibold text-xs shrink-0">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : <User size={16} />}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-gray-200 truncate">
                {user?.full_name || 'Analyst'}
              </p>
              <p className="text-[11px] text-gray-400 font-medium truncate">
                {formatRole(user?.role)}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            title="Sign Out"
            aria-label="Sign out"
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-ink-hover rounded-md transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
