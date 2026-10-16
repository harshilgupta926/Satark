import { copyFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const workerSource = path.join(root, 'node_modules', 'pdfjs-dist', 'build', 'pdf.worker.mjs');
const publicDir = path.join(root, 'public');
const workerDestination = path.join(publicDir, 'pdf.worker.mjs');

await mkdir(publicDir, { recursive: true });
await copyFile(workerSource, workerDestination);
console.log('Prepared same-origin PDF.js worker at /pdf.worker.mjs');
