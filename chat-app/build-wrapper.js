#!/usr/bin/env node
/**
 * Build wrapper for React application
 * Compatible with Node.js 18.x, 20.x, 22.x
 * For Plesk Obsidian 18.0.74 | AlmaLinux 9.7
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('🏗️  Starting React build...\n');

// Set environment variables for build
const env = {
  ...process.env,
  GENERATE_SOURCEMAP: 'false',
  NODE_OPTIONS: '--max-old-space-size=4096'
};

// Run react-scripts build
const buildProcess = spawn('npx', ['react-scripts', 'build'], {
  cwd: __dirname,
  env: env,
  stdio: 'inherit',
  shell: true
});

buildProcess.on('close', (code) => {
  if (code === 0) {
    console.log('\n✅ Build completed successfully!');
  } else {
    console.error(`\n❌ Build failed with code ${code}`);
    process.exit(code);
  }
});

buildProcess.on('error', (err) => {
  console.error('❌ Build process error:', err);
  process.exit(1);
});
