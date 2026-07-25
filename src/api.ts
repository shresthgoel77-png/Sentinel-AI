import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/v1',
});

// Global request interceptor injecting auth seamlessly without repeating in fetch blocks
api.interceptors.request.use((config) => {
    // Note: To expand into production JWT, we can pull token from Context mapping here
    config.headers.Authorization = `Bearer sk_sentinel_demo_key`;
    return config;
});

export default api;
