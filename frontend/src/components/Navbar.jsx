import React from "react";
import { Sparkles, Menu, Plus, Bot, User as UserIcon, MessageSquare, FileCode, BookOpen, Cpu } from "lucide-react";

export default function Navbar({
  onToggleSidebar,
  onNewChat,
  activeMode = "chat",
  onSelectMode,
  activeProvider = "gemini",
  onSelectProvider,
  userEmail = "dev@example.com",
}) {
  return (
    <header className="h-14 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-4 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleSidebar}
          className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          title="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
            <Sparkles className="w-4 h-4 text-slate-950 font-bold" />
          </div>
          <div className="hidden sm:block">
            <h1 className="font-semibold text-slate-100 text-sm tracking-wide">
              Lenny Growth Assistant
            </h1>
            <p className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
              <span>Transcript-Grounded RAG</span>
            </p>
          </div>
        </div>
      </div>

      {/* Center Mode Selector */}
      <div className="flex items-center bg-slate-900 border border-slate-800/80 p-1 rounded-xl space-x-1 shadow-inner">
        <button
          onClick={() => onSelectMode && onSelectMode("chat")}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 ${
            activeMode === "chat"
              ? "bg-amber-500 text-slate-950 shadow-md font-semibold"
              : "text-slate-400 hover:text-slate-200"
          }`}
          title="Normal podcast Q&A mode"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Chat</span>
        </button>
        <button
          onClick={() => onSelectMode && onSelectMode("artifacts")}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 ${
            activeMode === "artifacts"
              ? "bg-amber-500 text-slate-950 shadow-md font-semibold"
              : "text-slate-400 hover:text-slate-200"
          }`}
          title="Generate HTML/CSS artifacts & templates"
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>Artifacts</span>
        </button>
        <button
          onClick={() => onSelectMode && onSelectMode("ship30for30")}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 ${
            activeMode === "ship30for30"
              ? "bg-amber-500 text-slate-950 shadow-md font-semibold"
              : "text-slate-400 hover:text-slate-200"
          }`}
          title="Generate long-form Ship30for30 style essays"
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Ship30for30</span>
        </button>
      </div>

      {/* Right Provider Selector & User Info */}
      <div className="flex items-center space-x-3">
        <div className="hidden md:flex items-center space-x-1 bg-slate-900 border border-slate-800/90 p-1 rounded-xl">
          <span className="text-[10px] font-mono font-semibold text-slate-400 px-1.5 uppercase tracking-wider">LLM:</span>
          <button
            onClick={() => onSelectProvider && onSelectProvider("gemini")}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono transition flex items-center space-x-1 ${
              activeProvider === "gemini"
                ? "bg-amber-500 text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Use Google Gemini API"
          >
            <Sparkles className="w-3 h-3" />
            <span>Gemini</span>
          </button>
          <button
            onClick={() => onSelectProvider && onSelectProvider("anthropic")}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono transition flex items-center space-x-1 ${
              activeProvider === "anthropic"
                ? "bg-amber-500 text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Use Anthropic Claude API"
          >
            <Bot className="w-3 h-3" />
            <span>Anthropic</span>
          </button>
          <button
            onClick={() => onSelectProvider && onSelectProvider("ollama")}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono transition flex items-center space-x-1 ${
              activeProvider === "ollama"
                ? "bg-amber-500 text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Use Local Ollama Server"
          >
            <Cpu className="w-3 h-3" />
            <span>Ollama</span>
          </button>
        </div>

        <button
          onClick={onNewChat}
          className="md:hidden flex items-center space-x-1 text-xs font-medium bg-amber-500 text-slate-950 hover:bg-amber-400 px-3 py-1.5 rounded-lg transition"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New</span>
        </button>

        <div className="hidden lg:flex items-center space-x-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 rounded-full px-3 py-1">
          <UserIcon className="w-3.5 h-3.5 text-slate-400" />
          <span className="truncate max-w-[140px]">{userEmail}</span>
        </div>
      </div>
    </header>
  );
}


