import { NavLink, useNavigate } from 'react-router-dom';
import {
  Home,
  PlusCircle,
  FolderOpen,
  BarChart2,
  FileText,
  Settings,
  ShieldCheck,
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

  return (
    <aside
      id="workspace-navigation"
      className={`app-sidebar flex flex-col shrink-0 ${open ? 'is-open' : ''}`}
    >
      {/* Brand Header */}
      <div className="sidebar-brand flex items-center justify-between px-6 py-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-violet-600/30 border border-violet-500/40 text-violet-300 shadow-inner">
            <ShieldCheck size={20} className="text-violet-300" />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-white tracking-tight leading-tight">
              VisionForensics AI
            </h1>
            <p className="text-[11px] text-[#9E9AB8] font-normal leading-tight mt-0.5">
              Document Forgery Analysis
            </p>
          </div>
        </div>
        <button
          type="button"
          className="navigation-close text-gray-400 hover:text-white"
          onClick={onClose}
          aria-label="Close navigation"
        >
          <X size={18} />
        </button>
      </div>

      {/* Navigation Items */}
      <nav aria-label="Main navigation" className="flex-1 px-3.5 py-6 space-y-1">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `nav-item flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[13px] font-medium transition-all ${
                isActive
                  ? 'is-active bg-[#7045E8] text-white font-semibold shadow-md shadow-violet-900/30'
                  : 'text-[#A29EBC] hover:bg-white/[0.07] hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom Sign Out Bar */}
      <div className="p-3 mx-3 mb-4 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-between mt-auto">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-7 h-7 rounded-lg bg-violet-600/30 flex items-center justify-center text-xs font-bold text-violet-300">
            {user?.full_name ? user.full_name.charAt(0) : 'P'}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-white truncate">{user?.full_name || 'Pilot Analyst A'}</p>
            <p className="text-[10px] text-[#9E9AB8] truncate">{user?.role?.replace(/_/g, ' ') || 'Forensic Analyst'}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          title="Sign Out Session"
          aria-label="Sign out"
          className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-white/10 rounded-lg transition-colors"
        >
          <LogOut size={14} />
        </button>
      </div>
    </aside>
  );
}
