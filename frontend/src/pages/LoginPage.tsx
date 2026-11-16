import AuthShell from '@/components/AuthShell';
import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import {
  Lock,
  Mail,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  KeyRound,
  ArrowRight,
} from 'lucide-react';
import { extractApiError } from '@/utils/helpers';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fromLocation = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email.trim() || !password) {
      setErrorMessage('Please provide both email address and password.');
      return;
    }

    setIsLoading(true);
    try {
      await login({ email: email.trim(), password });
      navigate(fromLocation, { replace: true });
    } catch (err: unknown) {
      const parsed = extractApiError(err);
      setErrorMessage(parsed);
    } finally {
      setIsLoading(false);
    }
  };

  const fillQuickCredentials = (userEmail: string) => {
    setEmail(userEmail);
    setPassword('');
    setErrorMessage(null);
  };

  return (
    <AuthShell>
      <div className="auth-form-card">
        {/* Form body */}
        <div className="space-y-6">
          {errorMessage && (
            <div className="p-3.5 bg-severity-critical/10 border border-severity-critical/30 rounded-lg flex items-start gap-3 text-xs text-red-300">
              <AlertCircle size={18} className="text-severity-critical shrink-0 mt-0.5" />
              <div className="flex-1 font-medium leading-relaxed">{errorMessage}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="loginpage-field-1" className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                Analyst Email
              </label>
              <div className="relative">
                <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  id="loginpage-field-1"
                  type="email"
                  autoComplete="username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@visionforensics.local"
                  required
                  autoFocus
                  className="w-full bg-ink-base border border-ink-border rounded-lg pl-10 pr-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-all"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="loginpage-field-2" className="block text-xs font-semibold text-gray-300 uppercase tracking-wider">
                  Password
                </label>
              </div>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  id="loginpage-field-2"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full bg-ink-base border border-ink-border rounded-lg pl-10 pr-10 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-brand hover:bg-brand-hover disabled:opacity-50 text-white font-semibold text-sm rounded-lg shadow-md transition-all flex items-center justify-center gap-2 mt-2"
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Workspace</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Quick-fill pilot accounts helper */}
          <details className="reviewer-accounts pt-4 border-t border-ink-border">
            <summary className="text-xs font-medium text-muted cursor-pointer mb-3">
              <KeyRound size={13} className="text-brand" />
              Select reviewer email
            </summary>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => fillQuickCredentials('pilot_analyst_a@pilot.visionforensics.local')}
                className="p-2 text-left bg-ink-base/80 hover:bg-ink-hover border border-ink-border rounded-md text-gray-300 hover:text-white transition-colors"
              >
                <div className="font-semibold text-brand">Analyst A</div>
                <div className="text-[10px] text-gray-500 truncate">Forensic Examiner</div>
              </button>
              <button
                type="button"
                onClick={() => fillQuickCredentials('pilot_admin@pilot.visionforensics.local')}
                className="p-2 text-left bg-ink-base/80 hover:bg-ink-hover border border-ink-border rounded-md text-gray-300 hover:text-white transition-colors"
              >
                <div className="font-semibold text-amber-400">Administrator</div>
                <div className="text-[10px] text-gray-500 truncate">System Overseer</div>
              </button>
            </div>
          </details>

          {/* Registration link */}
          <div className="text-center text-xs text-gray-400 pt-2">
            Need an authorized account?{' '}
            <Link to="/register" className="text-brand hover:underline font-semibold">
              Register Analyst Account
            </Link>
          </div>
        </div>

      </div>
    </AuthShell>
  );
}
