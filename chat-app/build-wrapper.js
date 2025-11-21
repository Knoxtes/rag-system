#!/usr/bin/env node

// Build wrapper for Node.js 25.x compatibility
// Handles localStorage polyfill and OpenSSL legacy provider

const { LocalStorage } = require('node-localstorage');
const os = require('os');
const path = require('path');
const fs = require('fs');

// Create a temporary directory for localStorage
const tmpDir = path.join(os.tmpdir(), 'react-build-storage-' + Date.now());
if (!fs.existsSync(tmpDir)) {
  fs.mkdirSync(tmpDir, { recursive: true });
}

console.log('🔧 Setting up build environment for Node.js 25.x compatibility...');

// Polyfill global localStorage for Node.js 25.x
global.localStorage = new LocalStorage(tmpDir);
console.log('✅ localStorage polyfill ready');

// Set OpenSSL legacy provider for older dependencies
process.env.NODE_OPTIONS = '--openssl-legacy-provider';
console.log('✅ OpenSSL legacy provider enabled');

console.log('🏗️  Starting React build...\n');

// Now require and run react-scripts
process.argv = ['node', require.resolve('react-scripts/bin/react-scripts.js'), 'build'];
require('react-scripts/bin/react-scripts.js');
