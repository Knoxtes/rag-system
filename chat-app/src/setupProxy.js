const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests to Flask backend
  app.use(
    ['/auth', '/api', '/admin', '/chat', '/collections', '/status', '/static',
     '/folders', '/health', '/drive', '/cache', '/cost', '/force-init',
     '/switch-collection', '/refresh', '/test'],
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
    })
  );
};
