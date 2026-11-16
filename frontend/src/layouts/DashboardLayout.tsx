import { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '@/components/Sidebar';
import Topbar from '@/components/Topbar';

export default function DashboardLayout() {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const location = useLocation();
  useEffect(() => setNavigationOpen(false), [location.pathname]);
  useEffect(() => {
    if (!navigationOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setNavigationOpen(false);
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [navigationOpen]);
  return (
    <div className="app-shell flex min-h-screen bg-ink-base">
      <a href="#workspace-content" className="skip-link">Skip to workspace</a>
      {navigationOpen && <button className="navigation-scrim" aria-label="Close navigation" onClick={() => setNavigationOpen(false)} />}
      <Sidebar open={navigationOpen} onClose={() => setNavigationOpen(false)} />
      <div className="workspace-body flex flex-col flex-1 min-w-0">
        <Topbar navigationOpen={navigationOpen} onToggleNavigation={() => setNavigationOpen(!navigationOpen)} />
        <main id="workspace-content" tabIndex={-1} className="workspace-content flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
