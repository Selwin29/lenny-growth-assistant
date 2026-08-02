import React, { useState, useRef, useEffect } from "react";
import Message from "./Message";
import LoadingSpinner from "./LoadingSpinner";
import { Send, Sparkles, AlertCircle, RefreshCw, Compass } from "lucide-react";

const SUGGESTED_PROMPTS = [
  {
    title: "Product-Market Fit",
    prompt: "What does Lenny say about finding product-market fit?",
  },
  {
    title: "Startup Growth Strategy",
    prompt: "How should an early-stage startup think about growth acquisition channels?",
  },
  {
    title: "Ship30for30 Essay",
    prompt: "Write a Ship30for30-style essay on metrics that actually matter for product managers.",
  },
  {
    title: "Artifact Generation",
    prompt: "Create an HTML growth experiment dashboard template with CSS styling.",
  },
];

export default function ChatBox({
  messages = [],
  onSendMessage,
  isLoading = false,
  error = null,
  onRetry,
  onOpenArtifact,
}) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 overflow-hidden relative">
      {/* Scrollable Messages container */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800">
        {messages.length === 0 ? (
          /* Empty State */
          <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto space-y-6">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center shadow-xl shadow-amber-500/20">
              <Sparkles className="w-7 h-7 text-slate-950" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-slate-100">
                Lenny's Growth Assistant
              </h2>
              <p className="text-xs text-slate-400 max-w-md leading-relaxed">
                Ask product management, growth, and startup execution questions strictly answered from Lenny's Podcast transcripts.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
              {SUGGESTED_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setInput(item.prompt);
                    onSendMessage(item.prompt);
                  }}
                  className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/40 hover:bg-slate-900 text-left transition group"
                >
                  <div className="flex items-center space-x-2 text-xs font-semibold text-amber-400 mb-1">
                    <Compass className="w-3.5 h-3.5 group-hover:rotate-45 transition-transform" />
                    <span>{item.title}</span>
                  </div>
                  <p className="text-xs text-slate-300 line-clamp-2">
                    "{item.prompt}"
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Message List */
          <div className="pb-6">
            {messages.map((msg, index) => (
              <Message
                key={msg.id || index}
                message={msg}
                onOpenArtifact={onOpenArtifact}
              />
            ))}

            {isLoading && (
              <div className="py-5 px-4 md:px-6 bg-slate-900/60 border-y border-slate-800/40">
                <div className="max-w-3xl mx-auto flex items-center space-x-3 text-slate-400">
                  <LoadingSpinner size="sm" label="Analyzing transcripts and generating answer..." />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error state alert */}
      {error && (
        <div className="px-4 py-2 bg-rose-950/80 border-t border-rose-800/50 text-rose-200 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center space-x-1 font-medium bg-rose-900 hover:bg-rose-800 text-white px-2.5 py-1 rounded transition"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          )}
        </div>
      )}

      {/* Input area */}
      <div className="p-3 md:p-4 border-t border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a product or growth question from Lenny's Podcast..."
            rows={2}
            className="w-full bg-slate-900 text-slate-100 text-xs md:text-sm rounded-xl pl-4 pr-12 py-3 border border-slate-800 focus:border-amber-500/60 focus:ring-1 focus:ring-amber-500/30 focus:outline-none resize-none scrollbar-thin placeholder-slate-500"
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={`absolute right-3 bottom-3.5 p-2 rounded-lg transition ${
              input.trim() && !isLoading
                ? "bg-amber-500 text-slate-950 hover:bg-amber-400 cursor-pointer shadow-md shadow-amber-500/20"
                : "bg-slate-800 text-slate-500 cursor-not-allowed"
            }`}
            title="Send Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-[10px] text-center text-slate-400 mt-2 font-mono">
          Strictly grounded in Lenny's Podcast transcripts • Shift + Enter for new line
        </p>
      </div>
    </div>
  );
}
