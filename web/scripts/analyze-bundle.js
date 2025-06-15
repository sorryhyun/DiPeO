#!/usr/bin/env node

import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import process from 'node:process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distPath = path.join(__dirname, '../dist');

async function getFileSize(filePath) {
  const stats = await fs.stat(filePath);
  return stats.size;
}

function formatBytes(bytes) {
  const sizes = ['B', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 B';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

async function analyzeBuild() {
  try {
    const files = await fs.readdir(distPath, { recursive: true });
    const cssFiles = [];
    const jsFiles = [];
    let totalCssSize = 0;
    let totalJsSize = 0;

    for (const file of files) {
      const fullPath = path.join(distPath, file);
      const stats = await fs.stat(fullPath);
      
      if (stats.isFile()) {
        const size = await getFileSize(fullPath);
        
        if (file.endsWith('.css')) {
          cssFiles.push({ name: file, size });
          totalCssSize += size;
        } else if (file.endsWith('.js')) {
          jsFiles.push({ name: file, size });
          totalJsSize += size;
        }
      }
    }

    console.log('\n📊 Build Analysis Report\n');
    console.log('CSS Files:');
    console.log('----------');
    cssFiles.sort((a, b) => b.size - a.size).forEach(file => {
      console.log(`  ${file.name}: ${formatBytes(file.size)}`);
    });
    console.log(`\nTotal CSS: ${formatBytes(totalCssSize)}`);

    console.log('\nJS Files:');
    console.log('----------');
    jsFiles.sort((a, b) => b.size - a.size).forEach(file => {
      console.log(`  ${file.name}: ${formatBytes(file.size)}`);
    });
    console.log(`\nTotal JS: ${formatBytes(totalJsSize)}`);
    
    console.log(`\nTotal Build Size: ${formatBytes(totalCssSize + totalJsSize)}\n`);

    // Warnings
    if (totalCssSize > 50 * 1024) { // 50KB
      console.warn('⚠️  CSS bundle is larger than 50KB. Consider optimizing Tailwind config.');
    }
    
    if (cssFiles.some(f => f.name.includes('index') && f.size > 30 * 1024)) {
      console.warn('⚠️  Main CSS file is larger than 30KB. Check Tailwind safelist usage.');
    }

  } catch (error) {
    console.error('Error analyzing build:', error);
    process.exit(1);
  }
}

analyzeBuild();