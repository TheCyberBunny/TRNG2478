/**
 * Robopulse Command Center
 * Day 7 - a single shared Axios instance that every component uses
 * to talk to the FastAPI backend, instead of each component being
 * configured seperately
 */

import axios from 'axios';

//axios.create is a function that builds a reusable pre-configured client
const apiClient = axios.create({
    //this is our FastAPI endpoint
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
});

//the request interceptor runs on every outgoing request and checks if a token
//is sitting in localStorage. If so, it attaches it as the Authorization header
//automatically. Components do not need to remember to attach tokens, making this
//the centralized place for the token logic.
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('roboPulseToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}) ;

export default apiClient;