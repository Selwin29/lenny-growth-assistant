import React from "react";
import { Sparkles, Menu, Plus, Bot, User as UserIcon } from "lucide-react";

export default function Navbar({
  onToggleSidebar,
  onNewChat,
  activeProvider = "ollama",
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
          <div>
            <h1 className="font-semibold text-slate-100 text-sm tracking-wide">
              Lenny Growth Assistant
            </h1>
            <p className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
              <span>Transcript-Grounded RAG</span>
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <div className="hidden sm:flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-full px-3 py-1">
          <Bot className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-xs text-slate-300 font-mono capitalize">
            {activeProvider}
          </span>
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        </div>

        <button
          onClick={onNewChat}
          className="md:hidden flex items-center space-x-1 text-xs font-medium bg-amber-500 text-slate-950 hover:bg-amber-400 px-3 py-1.5 rounded-lg transition"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New</span>
        </button>

        <div className="hidden md:flex items-center space-x-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 rounded-full px-3 py-1">
          <UserIcon className="w-3.5 h-3.5 text-slate-400" />
          <span className="truncate max-w-[140px]">{userEmail}</span>
        </div>
      </div>
    </header>
  );
}
