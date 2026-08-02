import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { X, Code, Eye, Download, Copy, Check } from "lucide-react";

export default function ArtifactViewer({ artifact, onClose }) {
  const [viewMode, setViewMode] = useState("preview"); // "preview" | "code"
  const [copied, setCopied] = useState(false);

  if (!artifact) return null;

  const isHtml = artifact.artifact_type === "code" || artifact.content.trim().startsWith("<");

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = isHtml ? "html" : "md";
    const filename = `${artifact.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.${ext}`;
    const blob = new Blob([artifact.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full lg:w-[500px] xl:w-[600px] border-l border-slate-800 bg-slate-900 flex flex-col h-full overflow-hidden animate-slide-in relative shrink-0">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
        <div className="min-w-0">
          <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-amber-500">
            Artifact ({artifact.artifact_type})
          </span>
          <h3 className="text-sm font-semibold text-slate-100 truncate">
            {artifact.title || "Generated Artifact"}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-100 transition"
          title="Close panel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Control Actions bar */}
      <div className="px-4 py-2 bg-slate-900/60 border-b border-slate-800/40 flex items-center justify-between text-xs">
        <div className="flex bg-slate-950 p-0.5 rounded-lg border border-slate-800">
          <button
            onClick={() => setViewMode("preview")}
            className={`px-3 py-1 rounded-md font-medium transition flex items-center space-x-1.5 ${
              viewMode === "preview"
                ? "bg-slate-800 text-slate-100 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Preview</span>
          </button>
          <button
            onClick={() => setViewMode("code")}
            className={`px-3 py-1 rounded-md font-medium transition flex items-center space-x-1.5 ${
              viewMode === "code"
                ? "bg-slate-800 text-slate-100 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Code className="w-3.5 h-3.5" />
            <span>Code</span>
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="p-1.5 bg-slate-950/80 border border-slate-850 hover:border-slate-750 text-slate-300 hover:text-slate-100 rounded-lg transition"
            title="Copy Content"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 bg-slate-950/80 border border-slate-850 hover:border-slate-750 text-slate-300 hover:text-slate-100 rounded-lg transition"
            title="Download file"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main rendering area */}
      <div className="flex-1 overflow-y-auto bg-slate-950 scrollbar-thin">
        {viewMode === "preview" ? (
          isHtml ? (
            /* HTML sandboxed preview iframe */
            <iframe
              srcDoc={artifact.content}
              title="Artifact Preview"
              sandbox="allow-scripts"
              className="w-full h-full border-none bg-white"
            />
          ) : (
            /* Markdown rendering */
            <div className="p-6 prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed">
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || "");
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{
                          background: "#090d16",
                          padding: "1rem",
                          fontSize: "0.85rem",
                          borderRadius: "0.375rem",
                        }}
                        {...props}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
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
                {artifact.content}
              </ReactMarkdown>
            </div>
          )
        ) : (
          /* Raw source code display */
          <div className="h-full">
            <SyntaxHighlighter
              style={vscDarkPlus}
              language={isHtml ? "html" : "markdown"}
              PreTag="div"
              customStyle={{
                margin: 0,
                height: "100%",
                background: "#090d16",
                fontSize: "0.85rem",
                padding: "1rem",
              }}
            >
              {artifact.content}
            </SyntaxHighlighter>
          </div>
        )}
      </div>
    </div>
  );
}
