import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/v1',
});

// Global request interceptor injecting auth seamlessly without repeating in fetch blocks
api.interceptors.request.use((config) => {
    // Note: To expand into production JWT, we can pull token from Context mapping here
    config.headers.Authorization = `Bearer api_key_sentinel_demo`;
    return config;
});

export default api;
