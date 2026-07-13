const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || process.env.FRONTEND_PORT || 3000;
const FLASK_PORT = process.env.FLASK_PORT || process.env.BACKEND_PORT || 5001;

console.log('🔧 Server Configuration:');
console.log(`   Frontend Port: ${PORT}`);
console.log(`   Backend Port: ${FLASK_PORT}`);
console.log(`   Environment: ${process.env.NODE_ENV || 'development'}`);
console.log('');

// Start Flask backend
let flaskProcess;

function checkFlaskHealth(cb) {
  const http = require('http');
  const req = http.get(
    { hostname: '127.0.0.1', port: FLASK_PORT, path: '/health', timeout: 3000 },
    (res) => { res.resume(); cb(res.statusCode === 200); }
  );
  req.on('error', () => cb(false));
  req.on('timeout', () => { req.destroy(); cb(false); });
}

function startFlaskBackend() {
  console.log('🐍 Starting Flask backend...');

  // Use python or python3 depending on system
  const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';

  // --production: no debug mode, no Werkzeug auto-reloader (which forks a
  // second process and fights over the port)
  flaskProcess = spawn(pythonCommand, ['chat_api.py', '--production', '--port', FLASK_PORT, '--host', '127.0.0.1'], {
    cwd: __dirname,
    stdio: ['pipe', 'pipe', 'pipe'],
    // Lets Flask detect parent death (stdin EOF) and exit instead of orphaning
    env: { ...process.env, FLASK_MANAGED_BY_NODE: '1' }
  });

  flaskProcess.stdout.on('data', (data) => {
    console.log(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.stderr.on('data', (data) => {
    console.error(`[Flask Error] ${data.toString().trim()}`);
  });

  flaskProcess.on('close', (code) => {
    console.error(`Flask process exited with code ${code}`);
    flaskProcess = null;
    setTimeout(ensureFlaskBackend, 5000);
  });

  flaskProcess.on('error', (err) => {
    console.error('❌ Flask process error:', err);
  });
}

// Passenger may run several instances of this app. Only one should own the
// Flask backend; the others detect the healthy backend and just proxy to it.
let flaskProbeInFlight = false;
function ensureFlaskBackend() {
  if (flaskProbeInFlight) return;
  if (flaskProcess && flaskProcess.exitCode === null) return; // our child is alive
  flaskProbeInFlight = true;
  checkFlaskHealth((healthy) => {
    flaskProbeInFlight = false;
    if (healthy) {
      console.log('✅ Existing Flask backend detected on port', FLASK_PORT);
      return;
    }
    if (flaskProcess && flaskProcess.exitCode === null) return;
    startFlaskBackend();
  });
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down...');
  if (flaskProcess) {
    flaskProcess.kill();
  }
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Shutting down...');
  if (flaskProcess) {
    flaskProcess.kill();
  }
  process.exit(0);
});

// Start (or adopt) the Flask backend, and keep watching it
ensureFlaskBackend();
setInterval(ensureFlaskBackend, 15000);

// Serve static files from React build
const buildPath = path.join(__dirname, 'chat-app', 'build');
if (fs.existsSync(buildPath)) {
  app.use(express.static(buildPath));
  console.log('📁 Serving React build from:', buildPath);
} else {
  console.warn('⚠️  React build not found. Run "npm run build" first.');
}

// Health check for the Node.js server
app.get('/api/health', (req, res) => {
  // Proxy health check to Flask backend
  const http = require('http');
  const options = {
    hostname: '127.0.0.1',
    port: FLASK_PORT,
    path: '/health',
    method: 'GET'
  };

  const flaskReq = http.request(options, (flaskRes) => {
    let data = '';
    flaskRes.on('data', (chunk) => {
      data += chunk;
    });
    flaskRes.on('end', () => {
      try {
        const flaskHealth = JSON.parse(data);
        res.json({
          status: 'healthy',
          service: 'rag-system-unified',
          timestamp: new Date().toISOString(),
          node_server: 'running',
          flask_backend: flaskHealth.status,
          rag_initialized: flaskHealth.rag_initialized || false,
          backend_url: `http://127.0.0.1:${FLASK_PORT}`
        });
      } catch (error) {
        res.status(500).json({
          status: 'degraded',
          service: 'rag-system-unified',
          timestamp: new Date().toISOString(),
          node_server: 'running',
          flask_backend: 'error',
          rag_initialized: false,
          error: 'Flask backend not responding properly'
        });
      }
    });
  });

  flaskReq.on('error', () => {
    res.status(500).json({
      status: 'unhealthy',
      service: 'rag-system-unified',
      timestamp: new Date().toISOString(),
      node_server: 'running',
      flask_backend: 'disconnected',
      rag_initialized: false,
      error: 'Flask backend not available'
    });
  });

  flaskReq.setTimeout(5000, () => {
    flaskReq.destroy();
    res.status(500).json({
      status: 'timeout',
      service: 'rag-system-unified',
      timestamp: new Date().toISOString(),
      node_server: 'running',
      flask_backend: 'timeout',
      rag_initialized: false,
      error: 'Flask backend timeout'
    });
  });

  flaskReq.end();
});

// Proxy API requests to Flask backend
app.use('/auth', createProxyMiddleware({
  target: `http://127.0.0.1:${FLASK_PORT}`,
  changeOrigin: true,
  timeout: 30000,
  logLevel: 'warn',
  onError: (err, req, res) => {
    console.error('❌ Auth proxy error:', err.message);
    if (!res.headersSent) {
      res.status(503).json({
        error: 'Authentication service unavailable',
        message: 'The Python backend service is not responding. Please check if it is running.',
        timestamp: new Date().toISOString()
      });
    }
  }
}));

app.use('/chat', createProxyMiddleware({
  target: `http://127.0.0.1:${FLASK_PORT}`,
  changeOrigin: true,
  timeout: 60000, // Longer timeout for chat requests
  logLevel: 'warn',
  onError: (err, req, res) => {
    console.error('❌ Chat proxy error:', err.message);
    if (!res.headersSent) {
      res.status(503).json({
        error: 'Chat service unavailable',
        message: 'The chat backend is not responding.',
        timestamp: new Date().toISOString()
      });
    }
  }
}));

app.use('/collections', createProxyMiddleware({
  target: `http://127.0.0.1:${FLASK_PORT}`,
  changeOrigin: true,
  timeout: 30000,
  logLevel: 'warn'
}));

app.use('/folders', createProxyMiddleware({
  target: `http://127.0.0.1:${FLASK_PORT}`,
  changeOrigin: true,
  timeout: 30000,
  logLevel: 'warn'
}));

app.use('/switch-collection', createProxyMiddleware({
  target: `http://127.0.0.1:${FLASK_PORT}`,
  changeOrigin: true,
  timeout: 30000,
  logLevel: 'warn'
}));

app.use('/admin', createProxyMiddleware({
  target: `http://127.0.0.1:${FLASK_PORT}`,
  changeOrigin: true,
  timeout: 30000,
  logLevel: 'warn'
}));

app.use('/drive', createProxyMiddleware({
  target: `http://127.0.0.1:${FLASK_PORT}`,
  changeOrigin: true,
  timeout: 30000,
  logLevel: 'warn'
}));

app.use('/test', createProxyMiddleware({
  target: `http://127.0.0.1:${FLASK_PORT}`,
  changeOrigin: true,
  timeout: 30000,
  logLevel: 'warn'
}));

// Serve React app for all non-API routes
app.get('*', (req, res) => {
  const indexPath = path.join(buildPath, 'index.html');
  if (fs.existsSync(indexPath)) {
    res.sendFile(indexPath);
  } else {
    res.status(404).send(`
      <h1>RAG System</h1>
      <p>React build not found. Please run:</p>
      <pre>npm run build</pre>
      <p>Then restart the server.</p>
    `);
  }
});

app.listen(PORT, () => {
  console.log('🚀 RAG System starting...');
  console.log('=' .repeat(50));
  console.log(`🌐 Server running on port ${PORT}`);
  console.log(`🐍 Backend running on port ${FLASK_PORT}`);
  console.log(`📊 Health endpoint: /api/health`);
  console.log('=' .repeat(50));
  console.log('✅ Server is ready!');
});