import React, { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Sparkles, Mail, User as UserIcon, LogIn, AlertCircle } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionExpired = searchParams.get("expired") === "true";

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) {
      setError("Email address is required.");
      return;
    }

    setError("");
    setLoading(true);
    const result = await login(email.trim(), fullName.trim());
    setLoading(false);

    if (result.success) {
      navigate("/chat");
    } else {
      setError(result.error);
    }
  };

  // One-click developer quick login
  const handleDevLogin = async () => {
    setError("");
    setLoading(true);
    const result = await login("dev@example.com", "Development User");
    setLoading(false);

    if (result.success) {
      navigate("/chat");
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Visual background accents */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-orange-600/10 rounded-full blur-3xl" />

      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl relative z-10 space-y-6">
        {/* Brand logo & title */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center mx-auto shadow-lg shadow-amber-500/25">
            <Sparkles className="w-6 h-6 text-slate-950 font-bold" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100">Welcome back</h2>
          <p className="text-xs text-slate-400">
            Sign in to access your Lenny Growth Assistant sessions
          </p>
        </div>

        {/* Expired session notice */}
        {sessionExpired && (
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs rounded-xl flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Your session has expired. Please sign in again.</span>
          </div>
        )}

        {/* Error notification */}
        {error && (
          <div className="p-3 bg-rose-950/50 border border-rose-800/40 text-rose-200 text-xs rounded-xl flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300" htmlFor="email">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-slate-950 text-slate-100 placeholder-slate-600 text-xs md:text-sm rounded-xl pl-10 pr-4 py-2.5 border border-slate-800 focus:border-amber-500/60 focus:outline-none"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300" htmlFor="fullName">
              Full Name (Optional)
            </label>
            <div className="relative">
              <UserIcon className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
              <input
                id="fullName"
                type="text"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-slate-950 text-slate-100 placeholder-slate-600 text-xs md:text-sm rounded-xl pl-10 pr-4 py-2.5 border border-slate-800 focus:border-amber-500/60 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full inline-flex items-center justify-center space-x-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold py-2.5 rounded-xl text-xs md:text-sm shadow-xl transition transform active:scale-98"
          >
            <LogIn className="w-4 h-4" />
            <span>{loading ? "Authenticating..." : "Sign In with Email"}</span>
          </button>
        </form>

        <div className="relative flex items-center justify-center py-2">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-800" />
          </div>
          <span className="relative bg-slate-900 px-3 text-[10px] text-slate-500 font-mono">
            OR DEVELOPER ACCESS
          </span>
        </div>

        {/* Developer login bypass */}
        <button
          onClick={handleDevLogin}
          disabled={loading}
          className="w-full bg-slate-950 text-amber-400 border border-amber-500/20 hover:border-amber-500/40 hover:bg-slate-900/60 font-semibold py-2.5 rounded-xl text-xs transition"
        >
          Continue as Developer (dev@example.com)
        </button>
      </div>
    </div>
  );
}