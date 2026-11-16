import { useEffect, useState, type FormEvent } from 'react';
import api from '@/services/api';
import { extractApiError } from '@/utils/helpers';
import type { User, UserRole } from '@/types';

export default function UserManagement({ currentUserId }: { currentUserId: string }) {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('FORENSIC_ANALYST');
  const [page, setPage] = useState(0);
  const load = async (offset = page) => {
    setLoading(true);
    setError('');
    try { setUsers((await api.get<User[]>('/admin/users', { params: { skip: offset * 50, limit: 50 } })).data); }
    catch (err) { setError(extractApiError(err)); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(page); }, [page]);
  const create = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true); setError('');
    try {
      await api.post('/admin/users', { email, full_name: name, password, role });
      setPassword(''); setEmail(''); setName('');
      await load();
    } catch (err) { setError(extractApiError(err)); }
    finally { setBusy(false); }
  };
  const toggle = async (user: User) => {
    setBusy(true); setError('');
    try { await api.put(`/admin/users/${user.id}/status`, { is_active: !user.is_active }); await load(); }
    catch (err) { setError(extractApiError(err)); }
    finally { setBusy(false); }
  };
  const field = 'w-full rounded-lg border border-ink-border bg-ink-base px-3 py-2 text-sm';
  return <div className="space-y-6">
    <p className="text-sm text-muted">Administrator access. Account changes are recorded in the security audit log.</p>
    {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
    <form onSubmit={create} className="grid gap-4 sm:grid-cols-2">
      <label className="text-xs space-y-2"><span>Full name</span><input required maxLength={255} value={name} onChange={e => setName(e.target.value)} autoComplete="name" className={field} /></label>
      <label className="text-xs space-y-2"><span>Email</span><input required type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" className={field} /></label>
      <label className="text-xs space-y-2"><span>Initial password</span><input required type="password" minLength={12} value={password} onChange={e => setPassword(e.target.value)} autoComplete="new-password" className={field} /></label>
      <label className="text-xs space-y-2"><span>Role</span><select value={role} onChange={e => setRole(e.target.value as UserRole)} className={field}><option value="FORENSIC_ANALYST">Forensic analyst</option><option value="SENIOR_INVESTIGATOR">Senior investigator</option><option value="SYSTEM_ADMINISTRATOR">System administrator</option></select></label>
      <button disabled={busy} className="bg-brand text-white rounded-lg px-4 py-2 text-sm disabled:opacity-50 sm:col-span-2">{busy ? 'Saving…' : 'Create account'}</button>
    </form>
    {loading ? <p role="status" className="text-sm text-muted">Loading accounts…</p> : <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="text-muted border-b border-ink-border"><th className="py-3">Account</th><th>Role</th><th>Status</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>{users.map(user => <tr key={user.id} className="border-b border-ink-border"><td className="py-4 pr-4"><div className="font-semibold">{user.full_name}</div><div className="text-muted mt-1">{user.email}</div></td><td className="pr-4">{user.role.replace(/_/g, ' ').toLowerCase()}</td><td>{user.is_active ? 'Active' : 'Inactive'}</td><td className="text-right"><button disabled={busy || user.id === currentUserId} onClick={() => void toggle(user)} className="text-brand disabled:text-muted px-3 py-2">{user.id === currentUserId ? 'Your account' : user.is_active ? 'Deactivate' : 'Activate'}</button></td></tr>)}</tbody></table></div>}
    <div className="flex justify-between text-xs"><button disabled={page === 0 || loading} onClick={() => setPage(p => p - 1)} className="text-brand disabled:text-muted">Previous</button><span className="text-muted">Page {page + 1}</span><button disabled={users.length < 50 || loading} onClick={() => setPage(p => p + 1)} className="text-brand disabled:text-muted">Next</button></div>
  </div>;
}
