import React, { useState, useEffect, useCallback } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import ChatBox from "../components/ChatBox";
import ArtifactViewer from "../components/ArtifactViewer";
import LoadingSpinner from "../components/LoadingSpinner";
import { chatService } from "../services/chatService";
import { useAuth } from "../context/AuthContext";

export default function Chat() {
  const { user, logout } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeArtifact, setActiveArtifact] = useState(null);

  // 1. Fetch sessions list
  const fetchSessions = useCallback(async (autoSelectId = null) => {
    try {
      setLoadingSessions(true);
      setError(null);
      const data = await chatService.listSessions();
      setSessions(data);

      if (data.length > 0) {
        const targetId = autoSelectId || data[0].id;
        setActiveSessionId(targetId);
      } else {
        // Automatically create initial session if none exists
        const newSession = await chatService.createSession("New Chat");
        setSessions([newSession]);
        setActiveSessionId(newSession.id);
      }
    } catch (err) {
      console.error("Failed to load chat sessions:", err);
      setError("Failed to load chat sessions. Is the backend running?");
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // 2. Fetch session detail & messages when activeSessionId changes
  const fetchSessionMessages = useCallback(async (sessionId) => {
    if (!sessionId) return;
    try {
      setLoadingMessages(true);
      setError(null);
      const detail = await chatService.getSession(sessionId);
      setActiveSession(detail);
      setMessages(detail.messages || []);
    } catch (err) {
      console.error(`Failed to load session ${sessionId}:`, err);
      setError("Failed to load session history.");
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      fetchSessionMessages(activeSessionId);
    }
  }, [activeSessionId, fetchSessionMessages]);

  // Handle New Chat
  const handleNewChat = async () => {
    try {
      setError(null);
      const newSession = await chatService.createSession("New Chat");
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
    } catch (err) {
      console.error("Failed to create new chat session:", err);
      setError("Failed to create new chat.");
    }
  };

  // Handle Rename Chat
  const handleRenameSession = async (sessionId, newTitle) => {
    try {
      const updated = await chatService.updateSession(sessionId, newTitle);
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: updated.title } : s))
      );
      if (activeSessionId === sessionId) {
        setActiveSession((prev) => (prev ? { ...prev, title: updated.title } : prev));
      }
    } catch (err) {
      console.error(`Failed to rename session ${sessionId}:`, err);
      setError("Failed to rename session.");
    }
  };

  // Handle Delete Chat
  const handleDeleteSession = async (sessionId) => {
    try {
      await chatService.deleteSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);

      if (activeSessionId === sessionId) {
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
        } else {
          handleNewChat();
        }
      }
    } catch (err) {
      console.error(`Failed to delete session ${sessionId}:`, err);
      setError("Failed to delete session.");
    }
  };

  // Handle Send Message
  const handleSendMessage = async (content) => {
    if (!activeSessionId || sending) return;

    const tempUserMsg = {
      id: `temp-user-${Date.now()}`,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };

    // Optimistically show user message
    setMessages((prev) => [...prev, tempUserMsg]);
    setSending(true);
    setError(null);

    try {
      // 1. Post user message to backend
      const savedUserMsg = await chatService.sendMessage(activeSessionId, {
        role: "user",
        content,
      });

      // Replace temp message with persisted message
      setMessages((prev) =>
        prev.map((m) => (m.id === tempUserMsg.id ? savedUserMsg : m))
      );

      // 2. Fetch session messages to retrieve assistant response & artifacts
      await fetchSessionMessages(activeSessionId);

      // Auto-update session title if default "New Chat"
      if (
        activeSession &&
        (activeSession.title === "New Chat" || !activeSession.title)
      ) {
        const smartTitle =
          content.length > 30 ? content.slice(0, 30) + "..." : content;
        handleRenameSession(activeSessionId, smartTitle);
      }
    } catch (err) {
      console.error("Failed to send message:", err);
      setError("Failed to send message. Please check backend connection.");
    } finally {
      setSending(false);
    }
  };

  const handleRetry = () => {
    if (activeSessionId) {
      fetchSessionMessages(activeSessionId);
    } else {
      fetchSessions();
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Header Navbar */}
      <Navbar
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        onNewChat={handleNewChat}
        userEmail={user?.email || "dev@example.com"}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Sidebar */}
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onNewChat={handleNewChat}
          onRenameSession={handleRenameSession}
          onDeleteSession={handleDeleteSession}
          isOpen={sidebarOpen}
          onCloseMobile={() => setSidebarOpen(false)}
          userEmail={user?.email || "dev@example.com"}
          onLogout={logout}
        />

        {/* Chat Box */}
        {loadingSessions ? (
          <div className="flex-1 flex items-center justify-center">
            <LoadingSpinner size="lg" label="Connecting to Lenny Assistant backend..." />
          </div>
        ) : (
          <div className="flex-1 flex overflow-hidden relative">
            <ChatBox
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={sending || loadingMessages}
              error={error}
              onRetry={handleRetry}
              onOpenArtifact={setActiveArtifact}
            />
            {activeArtifact && (
              <ArtifactViewer
                artifact={activeArtifact}
                onClose={() => setActiveArtifact(null)}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}