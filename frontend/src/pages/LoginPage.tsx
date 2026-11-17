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
    setPassword('SmokeTestPassword2026!');
    setErrorMessage(null);
  };

  return (
    <AuthShell>
      <div className="space-y-5">
        {errorMessage && (
          <div className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl flex items-start gap-3 text-xs text-[#DC4545]">
            <AlertCircle size={18} className="text-[#DC4545] shrink-0 mt-0.5" />
            <div className="flex-1 font-medium leading-relaxed">{errorMessage}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="loginpage-field-1" className="block text-xs font-bold text-[#17172F] uppercase tracking-wider mb-1.5">
              Analyst Email
            </label>
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                id="loginpage-field-1"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@pilot.visionforensics.local"
                required
                autoFocus
                className="w-full bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-sm transition-all"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="loginpage-field-2" className="block text-xs font-bold text-[#17172F] uppercase tracking-wider">
                Password
              </label>
            </div>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                id="loginpage-field-2"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                className="w-full bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl pl-10 pr-10 py-2.5 text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-sm transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#73758B] hover:text-[#17172F] transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 px-4 bg-[#7045E8] hover:bg-[#5F33DB] disabled:opacity-50 text-white font-bold text-sm rounded-xl shadow-md shadow-violet-200 transition-all flex items-center justify-center gap-2 mt-2"
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
        <details className="pt-3 border-t border-[#E6E5F0]">
          <summary className="text-xs font-bold text-[#7045E8] cursor-pointer mb-2.5 flex items-center gap-1.5 select-none">
            <KeyRound size={13} />
            Quick Pilot Credentials
          </summary>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => fillQuickCredentials('pilot_analyst_a@pilot.visionforensics.local')}
              className="p-2.5 text-left bg-[#F8F9FF] hover:bg-[#F0EBFF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-xl text-[#17172F] transition-colors"
            >
              <div className="font-bold text-[#7045E8]">Analyst A</div>
              <div className="text-[10px] text-[#73758B]">Forensic Examiner</div>
            </button>
            <button
              type="button"
              onClick={() => fillQuickCredentials('pilot_admin@pilot.visionforensics.local')}
              className="p-2.5 text-left bg-[#F8F9FF] hover:bg-[#FFF8EC] border border-[#E6E5F0] hover:border-[#FFE8BF] rounded-xl text-[#17172F] transition-colors"
            >
              <div className="font-bold text-[#E9A12A]">Administrator</div>
              <div className="text-[10px] text-[#73758B]">System Overseer</div>
            </button>
          </div>
        </details>

        {/* Registration link */}
        <div className="text-center text-xs text-[#73758B] pt-1">
          Need an authorized account?{' '}
          <Link to="/register" className="text-[#7045E8] hover:underline font-bold">
            Register Analyst Account
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}
