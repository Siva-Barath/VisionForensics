import { useState, useEffect } from 'react';
import UserManagement from '@/components/UserManagement';
import ServiceHealthPanel from '@/components/ServiceHealthPanel';
import { checkHealth } from '@/services/api';
import type { HealthResponse } from '@/types';
import Card from '@/components/ui/Card';
import { Shield } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'governance' | 'modules' | 'profile' | 'security' | 'users'>('governance');

  const [health, setHealth] = useState<HealthResponse | null>(null);
  useEffect(() => { checkHealth().then(setHealth).catch(() => setHealth(null)); }, []);

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
    <div className="space-y-6 max-w-5xl">
      <div className="border-b border-ink-border pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-white">System Settings & Governance</h1>
        <p className="text-sm text-gray-400 mt-1">
          Review system parameters, cryptographic model invariants, and active forensic engine configurations.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Sidebar Tabs */}
        <div className="md:col-span-1">
          <div className="bg-ink-panel rounded-sm border border-ink-border overflow-hidden">
            <div className="divide-y divide-ink-border text-xs font-semibold">
              {[
                { id: 'governance', label: 'Model Governance' },
                { id: 'modules', label: 'Forensic Engines' },
                { id: 'profile', label: 'Examiner Profile' },
                { id: 'security', label: 'Security & Custody' },
                ...(user?.role === 'SYSTEM_ADMINISTRATOR' ? [{ id: 'users', label: 'User management' }] : []),
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`w-full text-left px-4 py-3 transition-colors ${
                    activeTab === tab.id
                      ? 'bg-brand/15 text-brand border-l-4 border-l-brand'
                      : 'text-gray-400 hover:bg-ink-hover hover:text-gray-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Tab Content */}
        <div className="md:col-span-3 space-y-6">
          {/* Tab 1: Model Governance */}
          {activeTab === 'governance' && (
            <Card variant="evidence" title="Model Invariants & Scientific Governance">
              <div className="p-5 space-y-6 text-xs">
                <div className="p-3 bg-brand/10 border border-brand/30 rounded-sm text-brand">
                  <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-[11px]">
                    <Shield size={14} className="text-brand" />
                    Strict Scientific Integrity Rule
                  </div>
                  <p className="mt-1 text-gray-300 leading-relaxed font-sans">
                    The operational decision threshold is locked at <strong className="text-white">T = 0.40</strong> to prevent analyst tuning bias. Models and schemas are cryptographically frozen.
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-ink-base rounded-sm border border-ink-border space-y-1">
                    <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                      Operational Decision Threshold
                    </span>
                    <div className="text-base font-bold font-mono text-white">T = 0.40 (Locked)</div>
                    <p className="text-[11px] text-gray-400">
                      Existing approved operational threshold. No recalibration was performed in this stabilization.
                    </p>
                  </div>

                  <div className="p-3 bg-ink-base rounded-sm border border-ink-border space-y-1 font-mono">
                    <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider font-sans">
                      Frozen Random Forest SHA-256 Digest
                    </span>
                    <div className="text-brand text-xs font-bold break-all">
                      f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280
                    </div>
                  </div>

                  <div className="p-3 bg-ink-base rounded-sm border border-ink-border space-y-1 font-mono">
                    <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider font-sans">
                      18-Feature Schema Integrity Checksum
                    </span>
                    <div className="text-emerald-400 text-xs font-bold break-all">
                      eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Tab 2: Forensic Engines */}
          {activeTab === 'modules' && (
            <Card variant="evidence" title="Active Forensic Inspection Engines">
              <ServiceHealthPanel health={health} />
            </Card>
          )}

          {/* Tab 3: Examiner Profile */}
          {activeTab === 'profile' && (
            <Card variant="evidence" title="Examiner Information">
              <div className="p-5 space-y-4 text-xs font-mono">
                <div className="flex items-center gap-3 pb-4 border-b border-ink-border font-sans">
                  <div className="w-12 h-12 rounded-full bg-brand/20 border border-brand flex items-center justify-center text-brand font-bold text-base">
                    {user?.full_name?.split(' ').map(n => n[0]).join('') || 'EX'}
                  </div>
                  <div>
                    <div className="text-base font-bold text-white font-sans">{user?.full_name || 'Examiner'}</div>
                    <div className="text-xs text-brand font-sans">{formatRole(user?.role)}</div>
                  </div>
                </div>

                <div className="space-y-2 text-gray-300">
                  <div className="flex justify-between py-1.5 border-b border-ink-border">
                    <span className="text-gray-400 font-sans">Account Email</span>
                    <span className="text-white">{user?.email || 'examiner@pilot.visionforensics.local'}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-ink-border">
                    <span className="text-gray-400 font-sans">Role Permission</span>
                    <span className="text-white font-sans">{formatRole(user?.role)}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-ink-border">
                    <span className="text-gray-400 font-sans">Deployment Tier</span>
                    <span className="text-white font-sans">Local Restricted Pilot</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-gray-400 font-sans">Account Status</span>
                    <span className="text-emerald-400 font-sans">Active & Authorized</span>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {activeTab === 'users' && user?.role === 'SYSTEM_ADMINISTRATOR' && <Card title="User management"><UserManagement currentUserId={user.id} /></Card>}
          {/* Tab 4: Security & Custody */}
          {activeTab === 'security' && (
            <Card variant="evidence" title="Security & Custody Invariants">
              <div className="p-5 space-y-3 text-xs">
                <div className="p-3 bg-ink-base rounded-sm border border-ink-border space-y-1">
                  <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                    Password Security
                  </span>
                  <div className="text-xs text-gray-200">Argon2id Memory-Hard Cryptographic Hashing</div>
                  <p className="text-[11px] text-gray-400">
                    Defends against offline GPU dictionary and brute-force password cracking attacks.
                  </p>
                </div>

                <div className="p-3 bg-ink-base rounded-sm border border-ink-border space-y-1">
                  <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                    Session Management
                  </span>
                  <div className="text-xs text-gray-200">15-Minute Ephemeral Access Tokens + 7-Day HttpOnly Refresh Rotation</div>
                  <p className="text-[11px] text-gray-400">
                    Refresh tokens rotate on use; access tokens expire according to the configured session policy.
                  </p>
                </div>

                <div className="p-3 bg-ink-base rounded-sm border border-ink-border space-y-1">
                  <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                    Evidence Tamper Alarm
                  </span>
                  <div className="text-xs text-emerald-400 font-semibold">SHA-256 verification on exhibit retrieval</div>
                  <p className="text-[11px] text-gray-400">
                    Every exhibit read verifies on-disk bytes against immutable SHA-256 custody digest. Mismatches trip HTTP 409 alarm.
                  </p>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
