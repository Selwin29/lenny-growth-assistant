import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { User, Sparkles, Copy, Check, FileCode, Layers } from "lucide-react";

export default function Message({ message, onOpenArtifact }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`py-5 px-4 md:px-6 transition ${
        isUser
          ? "bg-slate-950/40"
          : "bg-slate-900/60 border-y border-slate-800/40"
      }`}
    >
      <div className="max-w-3xl mx-auto flex items-start space-x-4">
        {/* Avatar */}
        <div className="shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center text-slate-950 shadow-md shadow-amber-500/20">
              <Sparkles className="w-4 h-4 font-bold" />
            </div>
          )}
        </div>

        {/* Content Box */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Header metadata */}
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold text-slate-200">
              {isUser ? "You" : "Lenny Growth Assistant"}
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleCopy}
                className="p-1 hover:text-slate-200 text-slate-400 transition rounded"
                title="Copy message"
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>

          {/* Rendered Body */}
          <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed font-sans">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  return !inline && match ? (
                    <div className="relative group my-3 rounded-lg overflow-hidden border border-slate-800 bg-slate-950">
                      <div className="bg-slate-900/80 px-3 py-1.5 text-[11px] text-slate-400 font-mono border-b border-slate-800 flex justify-between items-center">
                        <span>{match[1]}</span>
                      </div>
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{
                          margin: 0,
                          padding: "1rem",
                          background: "#090d16",
                          fontSize: "0.85rem",
                        }}
                        {...props}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code
                      className="bg-slate-800 text-amber-300 font-mono text-[0.85em] px-1.5 py-0.5 rounded"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Artifact Tag / Trigger (if artifact exists) */}
          {message.artifact && (
            <div className="mt-3">
              <button
                onClick={() => onOpenArtifact && onOpenArtifact(message.artifact)}
                className="inline-flex items-center space-x-2 bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/30 hover:border-amber-500/60 text-amber-300 px-3.5 py-2 rounded-xl text-xs font-medium transition group"
              >
                <Layers className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                <span>View Artifact: <strong>{message.artifact.title || "Generated Content"}</strong></span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
