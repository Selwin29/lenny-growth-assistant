import React, { useState } from "react";
import {
  MessageSquare,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  Sparkles,
  LogOut,
  ChevronRight,
  BookOpen,
} from "lucide-react";

export default function Sidebar({
  sessions = [],
  activeSessionId,
  onSelectSession,
  onNewChat,
  onRenameSession,
  onDeleteSession,
  isOpen,
  onCloseMobile,
  userEmail = "dev@example.com",
  onLogout,
}) {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  const startEditing = (e, session) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditTitle(session.title || "New Chat");
  };

  const handleSaveRename = async (e, sessionId) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      await onRenameSession(sessionId, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelRename = (e) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const handleDelete = async (e, sessionId) => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this chat session?")) {
      await onDeleteSession(sessionId);
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs z-30 md:hidden"
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-72 bg-slate-950 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Header / New Chat */}
        <div className="p-4 border-b border-slate-800/80">
          <button
            onClick={() => {
              onNewChat();
              onCloseMobile && onCloseMobile();
            }}
            className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-semibold py-2.5 px-4 rounded-xl shadow-lg shadow-amber-500/10 transition transform active:scale-98"
          >
            <Plus className="w-5 h-5 stroke-[2.5]" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Chat History Section */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin scrollbar-thumb-slate-800">
          <div className="px-3 py-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Conversations</span>
            <span className="text-slate-400 font-mono text-[10px]">
              {sessions.length}
            </span>
          </div>

          {sessions.length === 0 ? (
            <div className="text-center py-8 px-4 text-slate-400 text-xs">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p>No chat history yet.</p>
              <p className="text-[11px] mt-1 text-slate-400">Start a new chat to begin.</p>
            </div>
          ) : (
            sessions.map((session) => {
              const isActive = session.id === activeSessionId;
              const isEditing = session.id === editingId;

              return (
                <div
                  key={session.id}
                  onClick={() => {
                    if (!isEditing) {
                      onSelectSession(session.id);
                      onCloseMobile && onCloseMobile();
                    }
                  }}
                  className={`group relative flex items-center justify-between p-2.5 rounded-xl cursor-pointer text-xs transition ${
                    isActive
                      ? "bg-slate-800/90 text-amber-300 font-medium border border-slate-700/80 shadow-xs"
                      : "text-slate-300 hover:bg-slate-900 hover:text-slate-100"
                  }`}
                >
                  <div className="flex items-center space-x-2.5 truncate min-w-0 pr-2">
                    <MessageSquare
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? "text-amber-400" : "text-slate-400 group-hover:text-slate-300"
                      }`}
                    />

                    {isEditing ? (
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleSaveRename(e, session.id);
                          if (e.key === "Escape") handleCancelRename(e);
                        }}
                        autoFocus
                        className="bg-slate-900 text-slate-100 border border-amber-500/50 rounded px-1.5 py-0.5 text-xs w-full focus:outline-none"
                      />
                    ) : (
                      <span className="truncate">{session.title || "Untitled Chat"}</span>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-1 shrink-0">
                    {isEditing ? (
                      <>
                        <button
                          onClick={(e) => handleSaveRename(e, session.id)}
                          className="p-1 hover:text-emerald-400 text-slate-400"
                          title="Save"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={handleCancelRename}
                          className="p-1 hover:text-rose-400 text-slate-400"
                          title="Cancel"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </>
                    ) : (
                      <div className="opacity-0 group-hover:opacity-100 flex items-center space-x-0.5 transition-opacity">
                        <button
                          onClick={(e) => startEditing(e, session)}
                          className="p-1 text-slate-400 hover:text-slate-200 transition"
                          title="Rename"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, session.id)}
                          className="p-1 text-slate-400 hover:text-rose-400 transition"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer User Metadata */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/60 flex flex-col gap-2">
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800/60 text-xs">
            <div className="truncate pr-2">
              <p className="font-medium text-slate-200 truncate">{userEmail}</p>
              <p className="text-[10px] text-slate-400 font-mono">Lenny Growth AI</p>
            </div>
            <div className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" title="Connected" />
          </div>
          {onLogout && (
            <button
              onClick={onLogout}
              className="w-full flex items-center justify-center space-x-2 text-slate-400 hover:text-slate-100 hover:bg-slate-900/80 p-2 rounded-xl text-xs transition border border-transparent hover:border-slate-800/80"
            >
              <LogOut className="w-3.5 h-3.5 text-rose-400" />
              <span>Sign Out</span>
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
