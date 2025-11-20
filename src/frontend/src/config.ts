/**
 * Configuration for the frontend application
 */

// Backend API URL - can be overridden via environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const config = {
  /**
   * Base URL for the backend API.
   * - If empty string, uses relative URLs (same origin as frontend)
   * - If set to a URL (e.g., 'http://nas.local:8000'), all API calls will use that URL
   */
  apiBaseUrl: API_BASE_URL,

  /**
   * Full URL for chat endpoint
   */
  chatEndpoint: `${API_BASE_URL}/chat`,
};

export default config;
