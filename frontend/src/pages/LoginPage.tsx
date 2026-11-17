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
  ShieldCheck,
  User,
  Settings,
} from 'lucide-react';
import { extractApiError } from '@/utils/helpers';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
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
      {/* ===================================================================== */}
      {/* AUTHENTICATION CARD: Exact visual implementation of reference         */}
      {/* ===================================================================== */}
      <div className="bg-white rounded-3xl p-8 sm:p-10 shadow-xl border border-[#E6E5F0] w-full space-y-6">
        {/* Card Header */}
        <div className="space-y-1">
          {/* Secure Access Pill Badge */}
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F0EBFF] text-[#7045E8] border border-[#DDD5F9] text-xs font-semibold mb-1">
            <Lock size={12} className="text-[#7045E8]" />
            <span>Secure Access</span>
          </div>

          <h1 className="text-3xl font-extrabold text-[#17172F] tracking-tight">
            Welcome Back
          </h1>
          <p className="text-xs sm:text-sm text-[#73758B] mt-0.5">
            Sign in to your VisionForensics workspace
          </p>
        </div>

        {/* Error Alert Banner */}
        {errorMessage && (
          <div className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl flex items-start gap-2.5 text-xs text-[#DC4545] animate-in fade-in duration-200">
            <AlertCircle size={16} className="text-[#DC4545] shrink-0 mt-0.5" />
            <div className="flex-1 font-medium leading-relaxed">{errorMessage}</div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email Address Field */}
          <div className="space-y-1.5">
            <label 
              htmlFor="login-email" 
              className="block text-xs font-bold text-[#17172F]"
            >
              Email Address
            </label>
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                id="login-email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="pilot_analyst_a@pilot.visionforensics.local"
                required
                autoFocus
                className="w-full bg-white border border-[#E6E5F0] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#6D35E8] focus:ring-2 focus:ring-[#6D35E8]/10 shadow-xs transition-all"
              />
            </div>
          </div>

          {/* Password Field */}
          <div className="space-y-1.5">
            <label 
              htmlFor="login-password" 
              className="block text-xs font-bold text-[#17172F]"
            >
              Password
            </label>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                className="w-full bg-white border border-[#E6E5F0] rounded-xl pl-10 pr-10 py-2.5 text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#6D35E8] focus:ring-2 focus:ring-[#6D35E8]/10 shadow-xs transition-all font-mono"
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

          {/* Remember Me & Forgot Password Row */}
          <div className="flex items-center justify-between pt-0.5 text-xs">
            <label className="flex items-center gap-2 cursor-pointer select-none text-[#17172F] font-medium">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded text-[#6D35E8] focus:ring-[#6D35E8] border-[#DDD5F9] cursor-pointer"
              />
              <span>Remember me</span>
            </label>

            <button
              type="button"
              onClick={() => alert('Password recovery: Please contact your institutional system administrator to reset pilot credentials.')}
              className="text-[#6D35E8] hover:underline font-semibold"
            >
              Forgot password?
            </button>
          </div>

          {/* Primary Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 px-4 bg-gradient-to-r from-[#6D35E8] to-[#5922DA] hover:from-[#5F2CD1] hover:to-[#4C19C4] disabled:opacity-50 text-white font-bold text-sm rounded-xl shadow-md shadow-violet-500/25 transition-all flex items-center justify-center gap-2 mt-2"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <>
                <span className="text-base leading-none">→</span>
                <span>Sign In to Workspace</span>
              </>
            )}
          </button>
        </form>

        {/* Authorized Pilot Access Section */}
        <div className="space-y-3 pt-1">
          {/* Subtle Centered Divider */}
          <div className="relative text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#E6E5F0]" />
            </div>
            <span className="relative bg-white px-3 text-[11px] font-medium text-[#73758B]">
              Authorized Pilot Access
            </span>
          </div>

          {/* Two Side-by-Side Informational Role Cards (with quick-select) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {/* Analyst Account */}
            <button
              type="button"
              onClick={() => fillQuickCredentials('pilot_analyst_a@pilot.visionforensics.local')}
              className="p-3 text-left bg-[#F8F9FF] hover:bg-[#F0EBFF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-2xl transition-all flex items-center gap-3 group"
              title="Click to load Analyst credentials"
            >
              <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#6D35E8] group-hover:bg-white flex items-center justify-center shrink-0 transition-colors shadow-xs">
                <User size={18} />
              </div>
              <div className="min-w-0">
                <div className="font-bold text-xs text-[#17172F] group-hover:text-[#6D35E8] transition-colors truncate">
                  Analyst Account
                </div>
                <div className="text-[10px] text-[#73758B] leading-tight mt-0.5 truncate">
                  For investigation & analysis
                </div>
              </div>
            </button>

            {/* Administrator Account */}
            <button
              type="button"
              onClick={() => fillQuickCredentials('pilot_admin@pilot.visionforensics.local')}
              className="p-3 text-left bg-[#F8F9FF] hover:bg-[#F0EBFF] border border-[#E6E5F0] hover:border-[#DDD5F9] rounded-2xl transition-all flex items-center gap-3 group"
              title="Click to load Administrator credentials"
            >
              <div className="w-9 h-9 rounded-xl bg-[#F0EBFF] text-[#6D35E8] group-hover:bg-white flex items-center justify-center shrink-0 transition-colors shadow-xs">
                <Settings size={18} />
              </div>
              <div className="min-w-0">
                <div className="font-bold text-xs text-[#17172F] group-hover:text-[#6D35E8] transition-colors truncate">
                  Administrator Account
                </div>
                <div className="text-[10px] text-[#73758B] leading-tight mt-0.5 truncate">
                  System & model governance
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Security Footer */}
        <div className="flex items-center justify-center gap-3 text-[11px] text-[#73758B] font-medium pt-2 border-t border-[#F0EFF8]">
          <div className="flex items-center gap-1.5">
            <ShieldCheck size={14} className="text-[#159B55]" />
            <span>Argon2id Session Security</span>
          </div>
          <span className="text-[#DDD5F9]">|</span>
          <span>Encrypted (HTTPS)</span>
        </div>

        {/* Registration Helper Link */}
        <div className="text-center text-xs text-[#73758B] pt-1">
          Need an institutional account?{' '}
          <Link to="/register" className="text-[#6D35E8] hover:underline font-bold">
            Register Analyst Account
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}
