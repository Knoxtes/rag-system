#!/usr/bin/env node

// Polyfill localStorage for Node.js 25.x compatibility
const { LocalStorage } = require('node-localstorage');
const os = require('os');
const path = require('path');
const fs = require('fs');

// Create a temporary directory for localStorage
const tmpDir = path.join(os.tmpdir(), 'react-build-storage-' + Date.now());
if (!fs.existsSync(tmpDir)) {
  fs.mkdirSync(tmpDir, { recursive: true });
}

console.log('🔧 Setting up localStorage polyfill for Node 25.x...');

// Polyfill global localStorage
global.localStorage = new LocalStorage(tmpDir);

console.log('✅ localStorage polyfill ready');
console.log('🏗️  Starting React build...\n');

// Now require and run react-scripts
process.argv = ['node', require.resolve('react-scripts/bin/react-scripts.js'), 'build'];
require('react-scripts/bin/react-scripts.js');
