// Quick fix script to remove problematic client-side cache code
const fs = require('fs');

const appTsxPath = 'chat-app/src/App.tsx';
let content = fs.readFileSync(appTsxPath, 'utf8');

// Remove the problematic setRequestCache code
content = content.replace(/\s*\/\/ Cache the search result on client side[\s\S]*?return newCache;\s*}\);\s*/, '');

// Also remove formatFileSize function if unused
content = content.replace(/\s*\/\/ Format file size[\s\S]*?}\s*;/, '');

fs.writeFileSync(appTsxPath, content);
console.log('Frontend cache code removed successfully');