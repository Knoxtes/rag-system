#!/usr/bin/env node

// Polyfill localStorage for Node.js 25.x compatibility
const { LocalStorage } = require('node-localstorage');
const os = require('os');
const path = require('path');
const fs = require('fs');

// Create a temporary directory for localStorage
const tmpDir = path.join(os.tmpdir(), 'react-build-storage');
if (!fs.existsSync(tmpDir)) {
  fs.mkdirSync(tmpDir, { recursive: true });
}

// Polyfill global localStorage
global.localStorage = new LocalStorage(tmpDir);

// Now require and run react-scripts
process.argv = ['node', require.resolve('react-scripts/bin/react-scripts.js'), 'build'];
require('react-scripts/bin/react-scripts.js');
