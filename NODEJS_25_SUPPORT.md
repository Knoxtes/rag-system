# Node.js 25.x Support

## Overview

The RAG system **fully supports Node.js 25.x** (including version 25.2.0) through an automated compatibility wrapper. You can safely use Node.js 25.x in your Plesk environment.

---

## How It Works

### Automatic Compatibility Wrapper

The React build process uses `build-wrapper.js` which automatically handles Node.js 25.x compatibility issues:

1. **localStorage Polyfill**: Provides localStorage implementation for Node.js 25.x
2. **OpenSSL Legacy Provider**: Handles older crypto dependencies
3. **Transparent Operation**: Works automatically, no manual configuration needed

### Build Configuration

**File**: `chat-app/package.json`
```json
{
  "scripts": {
    "build": "node build-wrapper.js"
  },
  "devDependencies": {
    "node-localstorage": "^3.0.5"
  }
}
```

**File**: `chat-app/build-wrapper.js`
- Polyfills localStorage for Node.js 25.x
- Sets OpenSSL legacy provider
- Executes react-scripts build transparently

---

## Using Node.js 25.2.0 on Plesk

### Step 1: Enable Node.js 25.x in Plesk

1. Go to: **Domains → Ask.7MountainsMedia.com → Node.js**
2. Enable Node.js
3. Select version: **25.x**
4. Application mode: **production**
5. Click **Apply**

### Step 2: Clone and Setup

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git clone https://github.com/Knoxtes/rag-system.git .

# Run automated setup (automatically detects Node.js 25.x)
./setup-plesk.sh
```

The setup script will:
- ✅ Detect Node.js 25.x automatically
- ✅ Install node-localstorage dependency
- ✅ Build React app with compatibility wrapper
- ✅ No manual intervention needed

### Step 3: Manual Build (if needed)

If you need to rebuild manually:

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app

# Install dependencies (includes node-localstorage)
/opt/plesk/node/25/bin/npm install

# Build with wrapper (automatic compatibility)
/opt/plesk/node/25/bin/npm run build
```

**Expected Output:**
```
🔧 Setting up build environment for Node.js 25.x compatibility...
✅ localStorage polyfill ready
✅ OpenSSL legacy provider enabled
🏗️  Starting React build...

Creating an optimized production build...
Compiled successfully.

File sizes after gzip:
  184.6 kB  build/static/js/main.56634abc.js
  8.22 kB   build/static/css/main.f458a622.css
```

---

## Verification

### Check Node.js Version

```bash
/opt/plesk/node/25/bin/node --version
# Output: v25.2.0
```

### Test Build

```bash
cd chat-app
/opt/plesk/node/25/bin/npm run build

# Should complete without localStorage errors
# Build output: chat-app/build/
```

### Verify Dependencies

```bash
cd chat-app
npm list node-localstorage

# Should show:
# chat-app@0.1.0
# └── node-localstorage@3.0.5
```

---

## Troubleshooting

### Issue: "Cannot find module 'node-localstorage'"

**Cause**: Dependencies not installed

**Solution**:
```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app
/opt/plesk/node/25/bin/npm install
```

### Issue: Build still fails

**Solution**: Clean install
```bash
cd chat-app
rm -rf node_modules package-lock.json
/opt/plesk/node/25/bin/npm install
/opt/plesk/node/25/bin/npm run build
```

### Issue: "localStorage is not defined" error

**Cause**: Not using build-wrapper.js

**Solution**: Use the correct build script
```bash
# Correct (uses wrapper):
npm run build

# Incorrect (direct call):
# npm run build:legacy
```

---

## Technical Details

### What Was Fixed

**Previous Issue**: Node.js 25.x introduced a security restriction that prevents localStorage access without explicit configuration. This caused React build failures with error:
```
Failed to compile Security error cannot initialize local storage
```

**Solution Implemented**:
1. Added `node-localstorage` package to provide localStorage polyfill
2. Created `build-wrapper.js` that:
   - Creates temporary localStorage directory
   - Polyfills global.localStorage
   - Sets NODE_OPTIONS for OpenSSL compatibility
   - Transparently executes react-scripts build
3. Updated package.json to use wrapper by default

### Compatibility Matrix

| Node.js Version | Support Status | Notes |
|-----------------|----------------|-------|
| 18.x | ✅ Fully Supported | Stable, recommended for production |
| 20.x | ✅ Fully Supported | LTS, recommended for production |
| 22.x | ✅ Fully Supported | Latest LTS |
| 25.x | ✅ Fully Supported | Latest version, with automatic wrapper |

---

## Benefits of Node.js 25.x

### Why Use Node.js 25.x?

1. **Latest Features**: Access to newest JavaScript/TypeScript features
2. **Performance**: Improved V8 engine performance
3. **Security**: Latest security patches
4. **Future-Proof**: Stay current with Node.js development

### Our Compatibility Approach

- **Automatic**: No manual configuration needed
- **Transparent**: Works like any other Node.js version
- **Tested**: Build verified with Node.js 25.2.0
- **Maintained**: Wrapper updated as needed

---

## Migration from Older Versions

### From Node.js 18.x/20.x/22.x to 25.x

**No changes needed!** The build process works identically:

```bash
# Works with any version
npm install
npm run build
```

The build-wrapper.js automatically detects and handles Node.js 25.x requirements.

### Plesk Configuration

Update Node.js version in Plesk:
1. Domains → Ask.7MountainsMedia.com → Node.js
2. Change version from 22.x to 25.x
3. Click **Apply**
4. Click **Restart App**

Application continues working without code changes.

---

## Automated Setup Script Support

The `setup-plesk.sh` script fully supports Node.js 25.x:

```bash
# Automatically detects Node.js 25.x
./setup-plesk.sh

# Output includes:
# ✅ Found Plesk Node.js 25.x (with compatibility wrapper)
# ✅ React dependencies installed
# ✅ React app built successfully
```

The script prioritizes Node.js 25.x when available, as it's the latest version.

---

## Summary

✅ **Node.js 25.x is fully supported**  
✅ **Automatic compatibility wrapper**  
✅ **No manual configuration needed**  
✅ **Works with Plesk Obsidian 18.0.73**  
✅ **Tested with version 25.2.0**  
✅ **Production ready**

You can confidently use Node.js 25.x on your Plesk server running AlmaLinux 9.7 for Ask.7MountainsMedia.com.

---

**Last Updated**: November 2025  
**Verified With**: Node.js 25.2.0  
**Platform**: Plesk Obsidian 18.0.73 + AlmaLinux 9.7
