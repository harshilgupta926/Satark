import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('document review keeps parsing bounded and in-browser', async () => {
  const source = await readFile(new URL('../src/app/pdf-review/page.tsx', import.meta.url), 'utf8');
  assert.ok(source.includes('MAX_PDF_BYTES = 15 * 1024 * 1024'));
  assert.ok(source.includes('MAX_TEXT_BYTES = 2 * 1024 * 1024'));
  assert.ok(source.includes('MAX_PAGES = 50'));
  assert.ok(source.includes('MAX_TEXT_CHARS = 300_000'));
  assert.ok(source.includes('isEvalSupported: false'));
  assert.ok(source.includes("pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.mjs'"));
  assert.ok(source.includes("crypto.subtle.digest('SHA-256'"));
  assert.ok(!source.includes('fetch('), 'document content must not be sent over the network by this page');
  assert.ok(source.includes('OCR is not included'));
  assert.ok(source.includes('not evidence that the document is safe'));
});

test('media review bounds browser-local sampling and makes no authenticity claim', async () => {
  const source = await readFile(new URL('../src/app/media-review/page.tsx', import.meta.url), 'utf8');
  assert.ok(source.includes('MAX_VIDEO_BYTES = 50 * 1024 * 1024'));
  assert.ok(source.includes('MAX_VIDEO_SECONDS = 120'));
  assert.ok(source.includes('MAX_SAMPLE_COUNT = 6'));
  assert.ok(source.includes('video.currentTime = target'));
  assert.ok(source.includes('video.drawImage') === false);
  assert.ok(source.includes('context.drawImage(video, 0, 0, width, height)'));
  assert.ok(source.includes("crypto.subtle.digest('SHA-256'"));
  assert.ok(!source.includes('fetch('), 'video content must not be uploaded by this page');
  assert.ok(source.includes('not a deepfake'));
  assert.ok(source.includes('No file upload'));
});

test('capability directory links the implemented local document and media workflows', async () => {
  const source = await readFile(new URL('../src/app/tools/page.tsx', import.meta.url), 'utf8');
  assert.ok(source.includes("href: '/pdf-review'"));
  assert.ok(source.includes("href: '/media-review'"));
  assert.ok(source.includes('OCR for scanned PDFs'));
  assert.ok(source.includes('does not analyze audio'));
});
