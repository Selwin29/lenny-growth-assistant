import React from "react";
import { Link } from "react-router-dom";
import { Sparkles, MessageSquare, ArrowRight, BookOpen, Cpu, ShieldCheck } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-6 font-sans">
      {/* Header */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-4 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
            <Sparkles className="w-4 h-4 text-slate-950 font-bold" />
          </div>
          <span className="font-bold text-slate-100 text-base">Lenny Growth Assistant</span>
        </div>

        <Link
          to="/chat"
          className="flex items-center space-x-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-semibold px-4 py-2 rounded-xl text-xs shadow-lg transition"
        >
          <span>Open Assistant</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </header>

      {/* Main Hero */}
      <main className="max-w-4xl mx-auto text-center my-auto space-y-8 py-12">
        <div className="inline-flex items-center space-x-2 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs px-3.5 py-1.5 rounded-full font-mono">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Agentic AI Product Management & Growth Companion</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-100 leading-tight">
          Master Product & Growth with <br />
          <span className="bg-gradient-to-r from-amber-400 via-orange-400 to-amber-500 bg-clip-text text-transparent">
            Lenny's Podcast Transcripts
          </span>
        </h1>

        <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
          Ask questions, generate Ship30for30-style essays, and build HTML/CSS growth artifacts — strictly grounded in authentic podcast transcript knowledge.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            to="/chat"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold px-8 py-3.5 rounded-xl text-sm shadow-xl shadow-amber-500/20 transition transform active:scale-98"
          >
            <MessageSquare className="w-4 h-4" />
            <span>Start Chatting Now</span>
          </Link>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-10 text-left">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <BookOpen className="w-5 h-5 text-amber-400" />
            <h3 className="text-xs font-bold text-slate-200">Grounded Transcript RAG</h3>
            <p className="text-[11px] text-slate-400">Strict evidence-based answers with podcast episode source citations.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <Cpu className="w-5 h-5 text-orange-400" />
            <h3 className="text-xs font-bold text-slate-200">Local & Cloud LLMs</h3>
            <p className="text-[11px] text-slate-400">Run 100% offline with Ollama or connect Anthropic / OpenAI.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-xs font-bold text-slate-200">In-App Artifact Viewer</h3>
            <p className="text-[11px] text-slate-400">Render Markdown and HTML/CSS growth dashboards natively inside the app.</p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-4 border-t border-slate-800/80 text-[11px] text-slate-400 font-mono">
        Lenny Growth Assistant • Built with FastAPI, React, PostgreSQL & RAG
      </footer>
    </div>
  );
}