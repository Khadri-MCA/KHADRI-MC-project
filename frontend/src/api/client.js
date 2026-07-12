import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE || "http://localhost:8000/api",
  timeout: 35000, // fail fast instead of spinning forever if the backend/LLM hangs
});

export const searchHcps = (q) => api.get("/hcps", { params: { q } });
export const searchMaterials = (q) => api.get("/materials", { params: { q } });
export const createInteraction = (payload) => api.post("/interactions", payload);
export const updateInteraction = (id, payload) => api.patch(`/interactions/${id}`, payload);
export const sendChatMessage = (payload) => api.post("/chat", payload);

export default api;
