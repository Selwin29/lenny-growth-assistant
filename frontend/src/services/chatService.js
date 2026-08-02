import api from "./api";

export const chatService = {
  /**
   * Create a new chat session.
   * @param {string} [title="New Chat"]
   * @returns {Promise<Object>} Created session object
   */
  async createSession(title = "New Chat") {
    const response = await api.post("/chat/new", { title });
    return response.data;
  },

  /**
   * List all chat sessions for the current user.
   * @returns {Promise<Array>} List of session summaries
   */
  async listSessions() {
    const response = await api.get("/chat");
    return response.data;
  },

  /**
   * Get detail for a single chat session including messages.
   * @param {string} sessionId
   * @returns {Promise<Object>} Detailed session object with messages array
   */
  async getSession(sessionId) {
    const response = await api.get(`/chat/${sessionId}`);
    return response.data;
  },

  /**
   * Update chat session title.
   * @param {string} sessionId
   * @param {string} title
   * @returns {Promise<Object>} Updated session object
   */
  async updateSession(sessionId, title) {
    const response = await api.patch(`/chat/${sessionId}`, { title });
    return response.data;
  },

  /**
   * Delete a chat session.
   * @param {string} sessionId
   * @returns {Promise<void>}
   */
  async deleteSession(sessionId) {
    await api.delete(`/chat/${sessionId}`);
  },

  /**
   * Post a message to a session.
   * @param {string} sessionId
   * @param {Object} messageData { role: 'user' | 'assistant', content: string, mode?: string, provider?: string }
   * @returns {Promise<Object>} Created message object
   */
  async sendMessage(sessionId, { role = "user", content, mode, provider }) {
    const payload = { role, content };
    if (mode) payload.mode = mode;
    if (provider) payload.provider = provider;
    const response = await api.post(`/chat/${sessionId}/message`, payload);
    return response.data;
  },
};


