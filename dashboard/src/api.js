import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000" });

export const getStats = () => api.get("/violations/stats").then(r => r.data);
export const getViolations = (limit = 50) => api.get(`/violations?limit=${limit}`).then(r => r.data);
export const getBlacklist = () => api.get("/blacklist").then(r => r.data);
export const addToBlacklist = (word, category) => api.post("/blacklist", { word, category });
export const deleteFromBlacklist = (word) => api.delete(`/blacklist/${word}`);
export const getPending = () => api.get("/pending").then(r => r.data);
export const approveWord = (word) => api.post(`/pending/${encodeURIComponent(word)}/approve`);
export const rejectWord = (word) => api.post(`/pending/${encodeURIComponent(word)}/reject`);
