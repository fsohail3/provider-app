const API_CONFIG = {
    BASE_URL: process.env.NODE_ENV === 'production' 
        ? 'https://your-backend-render-url.onrender.com'
        : 'http://localhost:8000',
    
    ENDPOINTS: {
        QUERY: '/query',
        HEALTH: '/health'
    }
};

export default API_CONFIG; 