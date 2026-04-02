/**
 * Axios client for the FastAPI backend.
 * In development, Vite proxies /api → http://127.0.0.1:8000 (see vite.config.ts).
 * In production, set VITE_API_URL to your deployed API origin (e.g. https://api.example.com).
 */
import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? ''

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})
