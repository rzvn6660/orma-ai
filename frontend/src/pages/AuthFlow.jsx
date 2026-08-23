import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { authApi } from '../services/api';
import { 
  HeartPulse, 
  ShieldCheck, 
  Lock, 
  Mail, 
  ChevronRight, 
  UserCircle, 
  Users, 
  ArrowLeft, 
  Smartphone, 
  Pill, 
  Activity, 
  Mic, 
  LockKeyhole, 
  Globe, 
  Heart,
  Eye,
  EyeOff,
  Check,
  Sparkles
} from 'lucide-react';
import BrandLogo from '../components/BrandLogo';
import OtpInput from '../components/ui/OtpInput';

// Connected Interactive Family & ORMA Product Animation
const FamilyAnimation = ({ activeFeature }) => {
  return (
    <div className="relative w-full max-w-md aspect-square mx-auto flex items-center justify-center my-4">
      {/* Background glow responding to active feature */}
      <motion.div 
        animate={{ 
          scale: activeFeature ? [1, 1.15, 1] : [1, 1.05, 1], 
          opacity: activeFeature ? [0.6, 0.9, 0.6] : [0.4, 0.7, 0.4] 
        }} 
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        className={`absolute inset-0 rounded-full blur-3xl transition-colors duration-500 ${
          activeFeature === 'Voice AI' ? 'bg-gradient-to-tr from-cyan-500/30 to-blue-500/30' :
          activeFeature === 'Smart Reminders' ? 'bg-gradient-to-tr from-emerald-500/30 to-teal-500/30' :
          activeFeature === 'Family Connect' ? 'bg-gradient-to-tr from-purple-500/30 to-blue-500/30' :
          activeFeature === 'Emotional Wellness' ? 'bg-gradient-to-tr from-pink-500/30 to-rose-500/30' :
          activeFeature === 'Secure & Private' ? 'bg-gradient-to-tr from-indigo-500/30 to-purple-500/30' :
          'bg-gradient-to-tr from-purple-400/20 to-blue-400/20'
        }`} 
      />
      
      <div className="relative w-72 h-72 flex items-center justify-center">
        
        {/* Active Feature Badge Floating Overhead */}
        <AnimatePresence mode="wait">
          {activeFeature && (
            <motion.div
              key={activeFeature}
              initial={{ opacity: 0, y: -15, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.9 }}
              className="absolute -top-4 z-30 px-4 py-1.5 rounded-full bg-slate-900/90 text-white text-xs font-bold shadow-xl border border-purple-400/40 flex items-center gap-2 backdrop-blur-md"
            >
              <Sparkles className="w-3.5 h-3.5 text-purple-400 animate-spin" />
              <span>{activeFeature} Mode Active</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Central ORMA Hub / Family Core Visual */}
        <div className="relative w-56 h-56 flex items-end justify-center pb-6">
          
          {/* Grandmother (Soft Purple) */}
          <motion.div 
            initial={{ x: -60, opacity: 0 }} 
            animate={{ 
              x: -22, 
              opacity: 1,
              scale: activeFeature === 'Family Connect' || activeFeature === 'Voice AI' ? 1.08 : 1
            }} 
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="absolute z-10 flex flex-col items-center"
          >
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-300 via-purple-400 to-purple-600 shadow-lg border-2 border-white/80" />
            <div className="w-20 h-24 rounded-t-[40px] bg-gradient-to-br from-purple-400 to-purple-700 shadow-lg -mt-4" />
          </motion.div>

          {/* Grandfather (Calm Blue) */}
          <motion.div 
            initial={{ x: 60, opacity: 0 }} 
            animate={{ 
              x: 22, 
              opacity: 1,
              scale: activeFeature === 'Smart Reminders' || activeFeature === 'Emotional Wellness' ? 1.08 : 1 
            }} 
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="absolute z-10 flex flex-col items-center"
          >
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-300 via-blue-400 to-blue-600 shadow-lg border-2 border-white/80" />
            <div className="w-24 h-28 rounded-t-[40px] bg-gradient-to-br from-blue-400 to-blue-700 shadow-lg -mt-4" />
          </motion.div>

          {/* Girl Child (Warm Pink) */}
          <motion.div 
            initial={{ x: -100, y: 50, opacity: 0 }} 
            animate={{ x: -48, y: 10, opacity: 1 }} 
            transition={{ delay: 0.3, duration: 0.8, ease: "easeOut" }}
            className="absolute z-20 flex flex-col items-center"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-300 to-pink-500 shadow-lg border-2 border-white/80" />
            <div className="w-14 h-16 rounded-t-[30px] bg-gradient-to-br from-pink-400 to-pink-600 shadow-lg -mt-2" />
          </motion.div>

          {/* Boy Child (Cyan/Teal) */}
          <motion.div 
            initial={{ x: 100, y: 50, opacity: 0 }} 
            animate={{ x: 48, y: 10, opacity: 1 }} 
            transition={{ delay: 0.4, duration: 0.8, ease: "easeOut" }}
            className="absolute z-20 flex flex-col items-center"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-300 to-teal-500 shadow-lg border-2 border-white/80" />
            <div className="w-16 h-18 rounded-t-[30px] bg-gradient-to-br from-teal-400 to-teal-600 shadow-lg -mt-2" />
          </motion.div>

          {/* Floating Hearts */}
          <motion.div 
            animate={{ y: [-4, 4, -4], opacity: [0.7, 1, 0.7] }} 
            transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -top-3 right-8 text-pink-500 z-30"
          >
            <Heart className="w-7 h-7 fill-current drop-shadow-[0_0_12px_rgba(236,72,153,0.8)]" />
          </motion.div>
          
          <motion.div 
            animate={{ y: [4, -4, 4], opacity: [0.6, 0.9, 0.6] }} 
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -top-8 left-10 text-purple-400 z-30"
          >
            <Heart className="w-5 h-5 fill-current drop-shadow-[0_0_10px_rgba(168,85,247,0.8)]" />
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default function AuthFlow({ onLogin, onBack, initialView = 'login' }) {
  const [view, setView] = useState(initialView); // 'login', 'phone', 'otp', 'role', 'signup', 'forgot-password', 'reset-password', 'email-otp', 'verify-email'
  const [role, setRole] = useState('');
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [phoneData, setPhoneData] = useState({ phone: '', otp: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [showSignupPassword, setShowSignupPassword] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [hoveredFeature, setHoveredFeature] = useState(null);
  
  // Forgot password state
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSuccess, setForgotSuccess] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  
  // Reset password state
  const [resetPassword, setResetPassword] = useState('');
  const [resetConfirm, setResetConfirm] = useState('');
  const [resetSuccess, setResetSuccess] = useState(false);
  const [tokenValid, setTokenValid] = useState(null); // null=checking, true=valid, false=invalid

  // Email OTP verification state
  const [emailOtp, setEmailOtp] = useState('');
  const [verifyEmailAddress, setVerifyEmailAddress] = useState('');
  const [emailVerifySuccess, setEmailVerifySuccess] = useState(false);
  const [emailVerifyCooldown, setEmailVerifyCooldown] = useState(0);
  const [unverifiedLoginEmail, setUnverifiedLoginEmail] = useState('');

  // Link-based email token verification state
  const [tokenVerifyState, setTokenVerifyState] = useState(null); // null, 'loading', 'success', 'error'
  const [tokenVerifyMessage, setTokenVerifyMessage] = useState('');

  // Scroll to top on view changes
  useEffect(() => { window.scrollTo(0, 0); }, [view]);

  // Validate reset token when arriving at reset-password view
  useEffect(() => {
    if (view === 'reset-password') {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('token');
      if (!token) { setTokenValid(false); return; }
      authApi.validateResetToken(token)
        .then(() => setTokenValid(true))
        .catch(() => setTokenValid(false));
    }
  }, [view]);

  // Handle email verification token deep-link (/verify-email?token=...)
  useEffect(() => {
    if (view === 'verify-email') {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('token');
      if (!token) {
        setTokenVerifyState('error');
        setTokenVerifyMessage('Invalid or missing verification link.');
        return;
      }
      setTokenVerifyState('loading');
      authApi.verifyEmailToken(token)
        .then(() => {
          setTokenVerifyState('success');
        })
        .catch((err) => {
          setTokenVerifyState('error');
          setTokenVerifyMessage(err.response?.data?.detail || 'This verification link has expired or is invalid.');
        });
    }
  }, [view]);

  // Cooldown timers
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setTimeout(() => setResendCooldown(c => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [resendCooldown]);

  useEffect(() => {
    if (emailVerifyCooldown <= 0) return;
    const timer = setTimeout(() => setEmailVerifyCooldown(c => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [emailVerifyCooldown]);

  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;
    setError('');
    setLoading(true);
    try {
      await authApi.forgotPassword(forgotEmail);
      setForgotSuccess(true);
      setResendCooldown(30);
    } catch {
      // Always show safe message even on network error
      setForgotSuccess(true);
      setResendCooldown(30);
    } finally {
      setLoading(false);
    }
  };

  const handleResendForgot = async () => {
    if (resendCooldown > 0 || loading) return;
    setLoading(true);
    try {
      await authApi.forgotPassword(forgotEmail);
    } catch { /* always safe */ } finally {
      setLoading(false);
      setResendCooldown(30);
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;
    setError('');
    if (resetPassword !== resetConfirm) {
      setError('Passwords do not match.');
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (!token) { setError('Invalid reset link.'); return; }
    setLoading(true);
    try {
      await authApi.resetPassword(token, resetPassword);
      setResetSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password. The link may have expired.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailOtpSubmit = async (e) => {
    if (e) e.preventDefault();
    if (loading || emailOtp.length < 6) return;
    setError('');
    setLoading(true);
    try {
      await authApi.verifyEmailOtp(verifyEmailAddress, emailOtp);
      setEmailVerifySuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid verification code. Please check and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendEmailOtp = async () => {
    if (emailVerifyCooldown > 0 || loading) return;
    setError('');
    setLoading(true);
    try {
      await authApi.resendVerificationOtp(verifyEmailAddress);
      setEmailVerifyCooldown(60);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to resend verification code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Password requirements (shared for signup + reset)
  const checkPass = (p) => ({
    len: p.length >= 8,
    lower: /[a-z]/.test(p),
    upper: /[A-Z]/.test(p),
    num: /\d/.test(p),
    special: /[@$!%*?&]/.test(p),
  });
  const resetReqs = checkPass(resetPassword);

  const getAuthErrorMessage = (err) => {
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout') || !err.response) {
      return 'Unable to reach ORMA AI backend. Please try again.';
    }
    if (err.response?.status === 403 && err.response?.data?.detail?.includes('verify your email')) {
      return 'Please verify your email before signing in.';
    }
    if (err.response?.status === 401) {
      return 'Incorrect email or password.';
    }
    if (err.response?.status === 409) {
      return 'An account with this email already exists.';
    }
    if (err.response?.status === 400) {
      return err.response?.data?.detail || 'Invalid input format. Please check your credentials.';
    }
    if (err.response?.status === 429) {
      return err.response?.data?.detail || 'Too many attempts. Please try again later.';
    }
    if (err.response?.status >= 500) {
      return 'Server error during authentication. Please try again.';
    }
    return err.response?.data?.detail || 'Authentication failed. Please try again.';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;
    setError('');
    setUnverifiedLoginEmail('');
    setLoading(true);
    try {
      if (view === 'login') {
        const res = await authApi.login(formData.email, formData.password);
        localStorage.setItem('orma_token', res.access_token);
        onLogin(res.user);
      } else {
        const res = await authApi.signup({ ...formData, role });
        if (res.requires_verification) {
          setVerifyEmailAddress(formData.email);
          setEmailOtp('');
          setEmailVerifySuccess(false);
          setEmailVerifyCooldown(60);
          setView('email-otp');
        } else if (res.access_token) {
          localStorage.setItem('orma_token', res.access_token);
          onLogin(res.user);
        }
      }
    } catch (err) {
      if (err.response?.status === 403 && err.response?.data?.detail?.includes('verify your email')) {
        setUnverifiedLoginEmail(formData.email);
        setError('Please verify your email before signing in.');
      } else {
        setError(getAuthErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    setError('');
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    if (!googleClientId || googleClientId.includes('your_google_client_id')) {
      setError('Google Sign-In is not configured in environment variables.');
      return;
    }

    if (!window.google?.accounts?.id) {
      setError('Google SDK is loading. Please try again in a moment.');
      return;
    }

    setGoogleLoading(true);

    try {
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response) => {
          if (!response?.credential) {
            setError('Google authentication failed: No credential received.');
            setGoogleLoading(false);
            return;
          }

          try {
            const res = await authApi.googleLogin({ 
              id_token: response.credential, 
              role: role || null 
            });
            localStorage.setItem('orma_token', res.access_token);
            onLogin(res.user);
          } catch (err) {
            setError(err.response?.data?.detail || "Google authentication failed.");
          } finally {
            setGoogleLoading(false);
          }
        },
        auto_select: false,
        cancel_on_tap_outside: true
      });

      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed()) {
          setGoogleLoading(false);
          setError('Google Sign-In prompt suppressed by browser settings.');
        } else if (notification.isDismissedMoment()) {
          if (notification.getDismissedReason() !== 'credential_returned') {
            setGoogleLoading(false);
          }
        }
      });
    } catch (err) {
      setError('Failed to launch Google Sign-In: ' + err.message);
      setGoogleLoading(false);
    }
  };

  const handlePhoneRequest = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authApi.requestOtp(phoneData.phone);
      setView('otp');
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send OTP.");
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneVerify = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authApi.verifyOtp(phoneData.phone, phoneData.otp, role || 'elderly');
      localStorage.setItem('orma_token', res.access_token);
      onLogin(res.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid OTP code.");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  // Password requirements calculation
  const passLength = formData.password.length >= 8;
  const passLower = /[a-z]/.test(formData.password);
  const passUpper = /[A-Z]/.test(formData.password);
  const passNum = /\d/.test(formData.password);
  const passSpecial = /[@$!%*?&]/.test(formData.password);

  // Six Preserved Feature Cards
  const features = [
    { icon: Mic, label: 'Voice AI' },
    { icon: Users, label: 'Family Connect' },
    { icon: Pill, label: 'Smart Reminders' },
    { icon: HeartPulse, label: 'Emotional Wellness' },
    { icon: LockKeyhole, label: 'Secure & Private' },
    { icon: Globe, label: 'Multilingual' },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-800 font-sans flex flex-col lg:flex-row overflow-hidden selection:bg-purple-200 selection:text-purple-900">
      
      {/* 🚨 LEFT SIDE VISUAL SHOWCASE — PRESERVED, REFINE & ENHANCE */}
      <div className="lg:w-5/12 bg-gradient-to-br from-purple-100/70 via-[#F8FAFC] to-blue-100/70 relative flex flex-col justify-between p-8 md:p-14 border-b lg:border-b-0 lg:border-r border-slate-200/80">
        
        {/* Brand Header */}
        <div className="relative z-10 flex items-center justify-between w-full">
          {onBack && (
            <button 
              onClick={onBack} 
              className="text-slate-500 hover:text-purple-600 transition-colors p-2 -ml-2 rounded-full hover:bg-purple-100/80 cursor-pointer"
              aria-label="Back to landing"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <BrandLogo 
            className="h-9" 
            textClassName="text-2xl font-bold tracking-tight" 
            textColor="text-slate-900" 
            accentColor="text-purple-600" 
          />
        </div>

        {/* Central Core Content & Animated Visual */}
        <div className="relative z-10 my-8 lg:my-0 flex-1 flex flex-col justify-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
            <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight mb-4">
              Care. Connect. <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600">
                Remember.
              </span>
            </h1>
            <p className="text-base text-slate-600 max-w-md leading-relaxed mb-6 font-normal">
              Empowering senior independence with voice AI companion technology while keeping caregivers connected in real time.
            </p>
          </motion.div>

          {/* Interactive Family & ORMA Product Animation */}
          <FamilyAnimation activeFeature={hoveredFeature} />
        </div>

        {/* Six Feature Cards Grid (Connected to Visual via Hover) */}
        <div className="relative z-10 hidden lg:grid grid-cols-3 gap-3">
          {features.map((feat, idx) => {
            const isHovered = hoveredFeature === feat.label;
            return (
              <div 
                key={idx} 
                onMouseEnter={() => setHoveredFeature(feat.label)}
                onMouseLeave={() => setHoveredFeature(null)}
                className={`flex flex-col items-center justify-center p-3 rounded-2xl border transition-all cursor-pointer ${
                  isHovered 
                    ? 'bg-white shadow-md border-purple-300 scale-105 text-purple-700' 
                    : 'bg-white/60 backdrop-blur-sm border-slate-200/70 text-slate-600 hover:bg-white/90'
                }`}
              >
                <feat.icon className={`w-5 h-5 mb-1.5 transition-transform ${isHovered ? 'scale-110 text-purple-600' : 'text-purple-500'}`} />
                <span className="text-[10px] font-bold uppercase tracking-wider text-center">{feat.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 🚨 RIGHT SIDE AUTHENTICATION FORM — Inspired by 21st.dev signin-page & Create Account Form */}
      <div className="lg:w-7/12 flex flex-col justify-center items-center p-8 md:p-16 relative bg-white">
        
        {/* Subtle background glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-100/40 rounded-full blur-[100px] pointer-events-none" />
        
        <div className="w-full max-w-md relative z-10">
          <AnimatePresence mode="wait">
            
            {/* VIEW 1: LOGIN */}
            {view === 'login' && (
              <motion.div key="login" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Welcome Back</h2>
                  <p className="text-slate-500 text-sm">Sign in to your ORMA AI account.</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-semibold space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-500 shrink-0" />
                      <span>{error}</span>
                    </div>
                    {unverifiedLoginEmail && (
                      <div className="pt-2 border-t border-red-200/60 flex items-center justify-between">
                        <span className="text-xs text-red-600 font-normal">Need to verify?</span>
                        <button
                          type="button"
                          onClick={() => {
                            setVerifyEmailAddress(unverifiedLoginEmail);
                            setEmailOtp('');
                            setError('');
                            setView('email-otp');
                          }}
                          className="text-xs font-bold text-purple-700 hover:text-purple-900 underline underline-offset-2 cursor-pointer"
                        >
                          Enter Verification Code →
                        </button>
                      </div>
                    )}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 ml-1">Email Address</label>
                    <div className="relative flex items-center group">
                      <Mail className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="email" 
                        name="email" 
                        value={formData.email} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-4 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white focus:ring-4 focus:ring-purple-500/10 transition-all" 
                        placeholder="you@family.com" 
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2 ml-1">
                      <label htmlFor="login-password" className="block text-xs font-bold text-slate-700 uppercase tracking-wider">Password</label>
                      <button
                        type="button"
                        onClick={() => { setError(''); setForgotEmail(formData.email || ''); setView('forgot-password'); }}
                        className="text-xs font-semibold text-purple-600 hover:text-purple-800 hover:underline underline-offset-2 transition-colors cursor-pointer"
                      >
                        Forgot password?
                      </button>
                    </div>
                    <div className="relative flex items-center group">
                      <Lock className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type={showPassword ? "text" : "password"} 
                        name="password" 
                        value={formData.password} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-12 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white focus:ring-4 focus:ring-purple-500/10 transition-all" 
                        placeholder="••••••••" 
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 p-2 rounded-xl text-slate-400 hover:text-purple-600 transition-colors cursor-pointer z-10"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="w-5 h-5 text-purple-600" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  <button 
                    disabled={loading} 
                    type="submit" 
                    className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2 cursor-pointer text-base"
                  >
                    {loading ? 'Signing In...' : 'Sign In Securely'}
                  </button>
                </form>

                <div className="mt-8 flex items-center gap-4">
                  <div className="flex-1 h-px bg-slate-200" />
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">or continue with</span>
                  <div className="flex-1 h-px bg-slate-200" />
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3">
                  <button 
                    type="button" 
                    disabled={loading || googleLoading}
                    onClick={handleGoogleLogin} 
                    className="flex items-center justify-center gap-2 py-3.5 px-4 border-2 border-slate-200 hover:bg-slate-50 rounded-2xl transition-colors font-semibold text-sm text-slate-700 cursor-pointer disabled:opacity-60"
                  >
                    {googleLoading ? (
                      <span className="text-purple-600 text-xs font-bold">Connecting...</span>
                    ) : (
                      <>
                        <Globe className="w-4 h-4 text-purple-600" />
                        <span>Google</span>
                      </>
                    )}
                  </button>
                  <button 
                    type="button" 
                    onClick={() => setView('phone')} 
                    className="flex items-center justify-center gap-2 py-3.5 px-4 border-2 border-slate-200 hover:bg-slate-50 rounded-2xl transition-colors font-semibold text-sm text-slate-700 cursor-pointer"
                  >
                    <Smartphone className="w-4 h-4 text-blue-600" />
                    <span>Phone OTP</span>
                  </button>
                </div>

                <div className="mt-8 text-center">
                  <p className="text-sm text-slate-600 font-medium">
                    New to ORMA AI?{' '}
                    <button onClick={() => setView('role')} className="text-purple-600 font-bold hover:underline decoration-2 underline-offset-4 cursor-pointer">
                      Create an account
                    </button>
                  </p>
                </div>
              </motion.div>
            )}

            {/* VIEW 2: PHONE LOGIN */}
            {view === 'phone' && (
              <motion.div key="phone" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Phone Authentication</h2>
                  <p className="text-slate-500 text-sm">We'll send a secure one-time passcode.</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-semibold">
                    {error}
                  </div>
                )}

                <form onSubmit={handlePhoneRequest} className="space-y-5">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 ml-1">Phone Number</label>
                    <div className="relative flex items-center group">
                      <Smartphone className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="tel" 
                        value={phoneData.phone} 
                        onChange={(e) => setPhoneData({...phoneData, phone: e.target.value})} 
                        className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-4 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white transition-all" 
                        placeholder="+91 98765 43210" 
                      />
                    </div>
                  </div>
                  <button disabled={loading} type="submit" className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl transition-all shadow-lg flex items-center justify-center cursor-pointer text-base">
                    {loading ? 'Sending OTP...' : 'Send Verification OTP'}
                  </button>
                </form>

                <div className="mt-8 text-center">
                  <button onClick={() => setView('login')} className="text-slate-500 font-semibold text-sm hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                    <ArrowLeft className="w-4 h-4" /> Back to Sign In
                  </button>
                </div>
              </motion.div>
            )}

            {/* VIEW 3: OTP VERIFY */}
            {view === 'otp' && (
              <motion.div key="otp" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Enter Verification Code</h2>
                  <p className="text-slate-500 text-sm">Sent to {phoneData.phone}</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-semibold">
                    {error}
                  </div>
                )}

                <form onSubmit={handlePhoneVerify} className="space-y-6">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 text-center">
                      Enter 6-Digit Verification Code
                    </label>
                    <OtpInput
                      length={6}
                      value={phoneData.otp}
                      onChange={(otp) => setPhoneData({ ...phoneData, otp })}
                      error={Boolean(error)}
                    />
                  </div>
                  <button 
                    disabled={loading || phoneData.otp.length < 6} 
                    type="submit" 
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 rounded-2xl transition-all shadow-lg flex items-center justify-center gap-2 cursor-pointer text-base disabled:opacity-50"
                  >
                    {loading ? 'Verifying...' : 'Verify & Sign In'} <ChevronRight className="w-5 h-5" />
                  </button>
                </form>

                <div className="mt-8 text-center">
                  <button onClick={() => setView('phone')} className="text-slate-500 font-semibold text-sm hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                    <ArrowLeft className="w-4 h-4" /> Edit Phone Number
                  </button>
                </div>
              </motion.div>
            )}

            {/* VIEW 4: ROLE SELECTION FOR REGISTRATION */}
            {view === 'role' && (
              <motion.div key="role" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Create ORMA Account</h2>
                  <p className="text-slate-500 text-sm">Select your primary role to customize your interface.</p>
                </div>

                <div className="space-y-4">
                  <button 
                    onClick={() => { setRole('elderly'); setView('signup'); }}
                    className="w-full p-6 rounded-3xl border-2 border-slate-200 bg-slate-50/70 hover:bg-purple-50/80 hover:border-purple-300 transition-all flex items-start text-left gap-5 group cursor-pointer"
                  >
                    <div className="w-14 h-14 rounded-2xl bg-purple-100 text-purple-600 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                      <UserCircle className="w-8 h-8" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-slate-900 mb-1 group-hover:text-purple-700 transition-colors">Parent / Elderly User</h3>
                      <p className="text-xs text-slate-500 leading-relaxed">Access hands-free voice AI for medicine reminders, memory tracking, and daily companionship.</p>
                    </div>
                  </button>

                  <button 
                    onClick={() => { setRole('caregiver'); setView('signup'); }}
                    className="w-full p-6 rounded-3xl border-2 border-slate-200 bg-slate-50/70 hover:bg-blue-50/80 hover:border-blue-300 transition-all flex items-start text-left gap-5 group cursor-pointer"
                  >
                    <div className="w-14 h-14 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                      <ShieldCheck className="w-8 h-8" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-slate-900 mb-1 group-hover:text-blue-700 transition-colors">Child / Family Caregiver</h3>
                      <p className="text-xs text-slate-500 leading-relaxed">Remotely monitor medicine adherence, receive missed-dose alerts, and track wellness metrics.</p>
                    </div>
                  </button>
                </div>

                <div className="mt-8 text-center">
                  <button onClick={() => setView('login')} className="text-slate-500 font-semibold text-sm hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                    <ArrowLeft className="w-4 h-4" /> Already have an account? Sign In
                  </button>
                </div>
              </motion.div>
            )}

            {/* VIEW 5: REGISTRATION FORM (Inspired by 21st.dev Create Account Form) */}
            {view === 'signup' && (
              <motion.div key="signup" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-8">
                  <div className="inline-block px-3.5 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded-full uppercase tracking-wider mb-3">
                    {role === 'elderly' ? 'Elderly Account' : 'Caregiver Account'}
                  </div>
                  <h2 className="text-3xl font-extrabold text-slate-900 mb-1">Account Registration</h2>
                  <p className="text-slate-500 text-sm">Enter your details to create your secure ORMA account.</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-semibold">
                    {error}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Full Name */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 ml-1">Full Name</label>
                    <div className="relative flex items-center group">
                      <UserCircle className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="text" 
                        name="name" 
                        value={formData.name} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-4 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white transition-all" 
                        placeholder="Sarah Jenkins" 
                      />
                    </div>
                  </div>

                  {/* Email Address */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 ml-1">Email Address</label>
                    <div className="relative flex items-center group">
                      <Mail className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="email" 
                        name="email" 
                        value={formData.email} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-4 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white transition-all" 
                        placeholder="you@family.com" 
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 ml-1">Secure Password</label>
                    <div className="relative flex items-center group">
                      <Lock className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type={showSignupPassword ? "text" : "password"} 
                        name="password" 
                        value={formData.password} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-12 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white transition-all" 
                        placeholder="••••••••" 
                      />
                      <button
                        type="button"
                        onClick={() => setShowSignupPassword(!showSignupPassword)}
                        className="absolute right-3.5 p-2 rounded-xl text-slate-400 hover:text-purple-600 transition-colors cursor-pointer z-10"
                        aria-label={showSignupPassword ? "Hide password" : "Show password"}
                      >
                        {showSignupPassword ? <EyeOff className="w-5 h-5 text-purple-600" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  {/* Real Password Security Checklist */}
                  {formData.password.length > 0 && (
                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1 text-[11px] font-semibold">
                      <div className={`flex items-center gap-1.5 ${passLength ? 'text-emerald-600' : 'text-slate-400'}`}>
                        <Check className="w-3.5 h-3.5" /> At least 8 characters
                      </div>
                      <div className={`flex items-center gap-1.5 ${passUpper && passLower ? 'text-emerald-600' : 'text-slate-400'}`}>
                        <Check className="w-3.5 h-3.5" /> Uppercase & lowercase letters
                      </div>
                      <div className={`flex items-center gap-1.5 ${passNum ? 'text-emerald-600' : 'text-slate-400'}`}>
                        <Check className="w-3.5 h-3.5" /> At least one number
                      </div>
                      <div className={`flex items-center gap-1.5 ${passSpecial ? 'text-emerald-600' : 'text-slate-400'}`}>
                        <Check className="w-3.5 h-3.5" /> Special character (@$!%*?&)
                      </div>
                    </div>
                  )}

                  <button 
                    disabled={loading} 
                    type="submit" 
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 rounded-2xl transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2 mt-4 cursor-pointer text-base"
                  >
                    {loading ? 'Creating Account...' : 'Create Secure Account'} <ChevronRight className="w-5 h-5" />
                  </button>
                </form>

                <div className="mt-6 text-center">
                  <button onClick={() => setView('role')} className="text-slate-500 font-semibold text-sm hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                    <ArrowLeft className="w-4 h-4" /> Change Role Selection
                  </button>
                </div>
              </motion.div>
            )}

            {/* VIEW 6: FORGOT PASSWORD */}
            {view === 'forgot-password' && (
              <motion.div key="forgot-password" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>

                {!forgotSuccess ? (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-14 h-14 rounded-2xl bg-purple-100 flex items-center justify-center mx-auto mb-4">
                        <Mail className="w-7 h-7 text-purple-600" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Forgot your password?</h2>
                      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
                        Enter the email address associated with your ORMA account and we'll send you instructions to reset your password.
                      </p>
                    </div>

                    {error && (
                      <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-semibold">
                        {error}
                      </div>
                    )}

                    <form onSubmit={handleForgotSubmit} className="space-y-5">
                      <div>
                        <label htmlFor="forgot-email" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 ml-1">Email Address</label>
                        <div className="relative flex items-center group">
                          <Mail className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                          <input
                            id="forgot-email"
                            required
                            type="email"
                            value={forgotEmail}
                            onChange={(e) => setForgotEmail(e.target.value)}
                            className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-4 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white focus:ring-4 focus:ring-purple-500/10 transition-all"
                            placeholder="you@family.com"
                          />
                        </div>
                      </div>
                      <button
                        disabled={loading}
                        type="submit"
                        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 rounded-2xl transition-all shadow-lg flex items-center justify-center gap-2 cursor-pointer text-base"
                      >
                        {loading ? 'Sending...' : 'Send Reset Link'}
                      </button>
                    </form>

                    <div className="mt-8 text-center">
                      <button onClick={() => { setError(''); setView('login'); }} className="text-slate-500 font-semibold text-sm hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                        <ArrowLeft className="w-4 h-4" /> Back to Sign In
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-14 h-14 rounded-2xl bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                        <Check className="w-7 h-7 text-emerald-600" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Check your email</h2>
                      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
                        If an account exists for <strong className="text-slate-700">{forgotEmail}</strong>, we've sent instructions to reset your password.
                      </p>
                    </div>

                    <div className="p-5 bg-slate-50 border border-slate-200 rounded-2xl text-center mb-6">
                      <p className="text-slate-500 text-sm mb-3">Didn't receive the email?</p>
                      {resendCooldown > 0 ? (
                        <p className="text-slate-400 text-xs font-semibold">Resend available in {resendCooldown}s</p>
                      ) : (
                        <button
                          onClick={handleResendForgot}
                          disabled={loading}
                          className="text-purple-600 font-bold text-sm hover:underline underline-offset-2 cursor-pointer disabled:opacity-60"
                        >
                          {loading ? 'Sending...' : 'Resend email'}
                        </button>
                      )}
                    </div>

                    <div className="text-center">
                      <button onClick={() => { setForgotSuccess(false); setError(''); setView('login'); }} className="text-slate-500 font-semibold text-sm hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                        <ArrowLeft className="w-4 h-4" /> Back to Sign In
                      </button>
                    </div>
                  </>
                )}
              </motion.div>
            )}

            {/* VIEW 7: RESET PASSWORD (arrived via email link /reset-password?token=...) */}
            {view === 'reset-password' && (
              <motion.div key="reset-password" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>

                {/* Token checking state */}
                {tokenValid === null && (
                  <div className="text-center py-16">
                    <div className="w-10 h-10 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-500 text-sm">Verifying reset link...</p>
                  </div>
                )}

                {/* Invalid / expired token */}
                {tokenValid === false && (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-14 h-14 rounded-2xl bg-red-100 flex items-center justify-center mx-auto mb-4">
                        <Lock className="w-7 h-7 text-red-500" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Link Expired</h2>
                      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
                        This password reset link is invalid or has expired. Please request a new one.
                      </p>
                    </div>
                    <button
                      onClick={() => { setTokenValid(null); setView('forgot-password'); }}
                      className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold py-4 rounded-2xl transition-all shadow-lg cursor-pointer text-base"
                    >
                      Request New Reset Link
                    </button>
                  </>
                )}

                {/* Valid token — show form */}
                {tokenValid === true && !resetSuccess && (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-14 h-14 rounded-2xl bg-purple-100 flex items-center justify-center mx-auto mb-4">
                        <Lock className="w-7 h-7 text-purple-600" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Reset your password</h2>
                      <p className="text-slate-500 text-sm">Create a new password for your ORMA AI account.</p>
                    </div>

                    {error && (
                      <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-semibold">
                        {error}
                      </div>
                    )}

                    <form onSubmit={handleResetSubmit} className="space-y-4">
                      <div>
                        <label htmlFor="reset-pw" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 ml-1">New Password</label>
                        <div className="relative flex items-center group">
                          <Lock className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                          <input
                            id="reset-pw"
                            required
                            type={showResetPassword ? 'text' : 'password'}
                            value={resetPassword}
                            onChange={(e) => setResetPassword(e.target.value)}
                            className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-12 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white transition-all"
                            placeholder="••••••••"
                          />
                          <button
                            type="button"
                            onClick={() => setShowResetPassword(!showResetPassword)}
                            className="absolute right-3.5 p-2 rounded-xl text-slate-400 hover:text-purple-600 transition-colors cursor-pointer z-10"
                            aria-label={showResetPassword ? 'Hide password' : 'Show password'}
                          >
                            {showResetPassword ? <EyeOff className="w-5 h-5 text-purple-600" /> : <Eye className="w-5 h-5" />}
                          </button>
                        </div>
                      </div>

                      <div>
                        <label htmlFor="reset-confirm" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 ml-1">Confirm New Password</label>
                        <div className="relative flex items-center group">
                          <Lock className="absolute left-4 w-5 h-5 text-slate-400 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                          <input
                            id="reset-confirm"
                            required
                            type={showResetConfirm ? 'text' : 'password'}
                            value={resetConfirm}
                            onChange={(e) => setResetConfirm(e.target.value)}
                            className="w-full h-14 bg-slate-50 border-2 border-slate-200 rounded-2xl pl-12 pr-12 text-slate-900 font-semibold text-base placeholder:text-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white transition-all"
                            placeholder="••••••••"
                          />
                          <button
                            type="button"
                            onClick={() => setShowResetConfirm(!showResetConfirm)}
                            className="absolute right-3.5 p-2 rounded-xl text-slate-400 hover:text-purple-600 transition-colors cursor-pointer z-10"
                            aria-label={showResetConfirm ? 'Hide password' : 'Show password'}
                          >
                            {showResetConfirm ? <EyeOff className="w-5 h-5 text-purple-600" /> : <Eye className="w-5 h-5" />}
                          </button>
                        </div>
                      </div>

                      {/* Real-time password requirements */}
                      {resetPassword.length > 0 && (
                        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1 text-[11px] font-semibold">
                          <div className={`flex items-center gap-1.5 ${resetReqs.len ? 'text-emerald-600' : 'text-slate-400'}`}>
                            <Check className="w-3.5 h-3.5" /> At least 8 characters
                          </div>
                          <div className={`flex items-center gap-1.5 ${resetReqs.upper && resetReqs.lower ? 'text-emerald-600' : 'text-slate-400'}`}>
                            <Check className="w-3.5 h-3.5" /> Uppercase &amp; lowercase letters
                          </div>
                          <div className={`flex items-center gap-1.5 ${resetReqs.num ? 'text-emerald-600' : 'text-slate-400'}`}>
                            <Check className="w-3.5 h-3.5" /> At least one number
                          </div>
                          <div className={`flex items-center gap-1.5 ${resetReqs.special ? 'text-emerald-600' : 'text-slate-400'}`}>
                            <Check className="w-3.5 h-3.5" /> Special character (@$!%*?&amp;)
                          </div>
                          {resetConfirm.length > 0 && (
                            <div className={`flex items-center gap-1.5 ${resetPassword === resetConfirm ? 'text-emerald-600' : 'text-red-500'}`}>
                              <Check className="w-3.5 h-3.5" /> Passwords match
                            </div>
                          )}
                        </div>
                      )}

                      <button
                        disabled={loading}
                        type="submit"
                        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 rounded-2xl transition-all shadow-lg flex items-center justify-center gap-2 mt-2 cursor-pointer text-base"
                      >
                        {loading ? 'Resetting password...' : 'Reset Password'} <ChevronRight className="w-5 h-5" />
                      </button>
                    </form>
                  </>
                )}

                {/* Success state after reset */}
                {tokenValid === true && resetSuccess && (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-14 h-14 rounded-2xl bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                        <Check className="w-7 h-7 text-emerald-600" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Password reset</h2>
                      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
                        Your ORMA AI password has been updated successfully. You can now sign in with your new password.
                      </p>
                    </div>
                    <button
                      onClick={() => { setResetSuccess(false); setResetPassword(''); setResetConfirm(''); setView('login'); if (onBack) onBack(); }}
                      className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl transition-all shadow-lg cursor-pointer text-base"
                    >
                      Sign In
                    </button>
                  </>
                )}
              </motion.div>
            )}

            {/* VIEW 8: EMAIL OTP VERIFICATION */}
            {view === 'email-otp' && (
              <motion.div key="email-otp" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                {!emailVerifySuccess ? (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-16 h-16 rounded-3xl bg-purple-100 flex items-center justify-center mx-auto mb-4 text-purple-600 shadow-inner">
                        <Mail className="w-8 h-8" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Check your email</h2>
                      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
                        Enter the 6-digit verification code we sent to <strong className="text-slate-800 font-semibold">{verifyEmailAddress}</strong>
                      </p>
                    </div>

                    {error && (
                      <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-semibold flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-red-500 shrink-0" />
                        <span>{error}</span>
                      </div>
                    )}

                    <form onSubmit={handleEmailOtpSubmit} className="space-y-6">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 text-center">
                          Enter 6-Digit Code
                        </label>
                        <OtpInput
                          length={6}
                          value={emailOtp}
                          onChange={(otp) => { setEmailOtp(otp); setError(''); }}
                          error={Boolean(error)}
                        />
                        <p className="text-center text-xs text-slate-400 font-medium mt-3">
                          Code expires in 5 minutes.
                        </p>
                      </div>

                      <button
                        disabled={loading || emailOtp.length < 6}
                        type="submit"
                        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 rounded-2xl transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2 cursor-pointer text-base disabled:opacity-50"
                      >
                        {loading ? 'Verifying...' : 'Verify Email'} <ChevronRight className="w-5 h-5" />
                      </button>
                    </form>

                    <div className="p-5 bg-slate-50 border border-slate-200 rounded-2xl text-center mt-6">
                      <p className="text-slate-500 text-sm mb-3">Didn't receive the code?</p>
                      {emailVerifyCooldown > 0 ? (
                        <p className="text-slate-400 text-xs font-semibold">
                          Resend available in <span className="text-purple-600 font-bold">{emailVerifyCooldown}s</span>
                        </p>
                      ) : (
                        <button
                          onClick={handleResendEmailOtp}
                          disabled={loading}
                          className="text-purple-600 font-bold text-sm hover:underline underline-offset-2 cursor-pointer disabled:opacity-60"
                        >
                          {loading ? 'Sending...' : 'Resend Code'}
                        </button>
                      )}
                    </div>

                    <div className="mt-6 text-center">
                      <button
                        onClick={() => { setError(''); setView('login'); }}
                        className="text-slate-500 font-semibold text-sm hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer"
                      >
                        <ArrowLeft className="w-4 h-4" /> Back to Sign In
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-16 h-16 rounded-3xl bg-emerald-100 flex items-center justify-center mx-auto mb-4 text-emerald-600 shadow-inner">
                        <Check className="w-8 h-8" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Email Verified</h2>
                      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
                        Your email has been verified successfully. You can now sign in to your ORMA AI account.
                      </p>
                    </div>

                    <button
                      onClick={() => {
                        setEmailVerifySuccess(false);
                        setError('');
                        setFormData(prev => ({ ...prev, email: verifyEmailAddress }));
                        setView('login');
                      }}
                      className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl transition-all shadow-lg hover:shadow-xl cursor-pointer text-base"
                    >
                      Continue to Sign In
                    </button>
                  </>
                )}
              </motion.div>
            )}

            {/* VIEW 9: LINK-BASED EMAIL VERIFICATION (/verify-email?token=...) */}
            {view === 'verify-email' && (
              <motion.div key="verify-email" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                {tokenVerifyState === 'loading' && (
                  <div className="text-center py-16">
                    <div className="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">Verifying your email...</h2>
                    <p className="text-slate-500 text-sm">Please wait while we confirm your email address.</p>
                  </div>
                )}

                {tokenVerifyState === 'error' && (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-16 h-16 rounded-3xl bg-red-100 flex items-center justify-center mx-auto mb-4 text-red-500 shadow-inner">
                        <Lock className="w-8 h-8" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Verification Failed</h2>
                      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
                        {tokenVerifyMessage || 'This verification link has expired or is invalid.'}
                      </p>
                    </div>

                    <div className="space-y-3">
                      <button
                        onClick={() => { setError(''); setView('email-otp'); }}
                        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 rounded-2xl transition-all shadow-lg cursor-pointer text-base"
                      >
                        Enter Verification Code
                      </button>
                      <button
                        onClick={() => { setError(''); setView('login'); }}
                        className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-3.5 rounded-2xl transition-all cursor-pointer text-sm"
                      >
                        Back to Sign In
                      </button>
                    </div>
                  </>
                )}

                {tokenVerifyState === 'success' && (
                  <>
                    <div className="text-center mb-8">
                      <div className="w-16 h-16 rounded-3xl bg-emerald-100 flex items-center justify-center mx-auto mb-4 text-emerald-600 shadow-inner">
                        <Check className="w-8 h-8" />
                      </div>
                      <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Email Verified</h2>
                      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
                        Your email has been verified successfully. You can now sign in to your ORMA AI account.
                      </p>
                    </div>

                    <button
                      onClick={() => {
                        setError('');
                        setView('login');
                      }}
                      className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl transition-all shadow-lg hover:shadow-xl cursor-pointer text-base"
                    >
                      Continue to Sign In
                    </button>
                  </>
                )}
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
