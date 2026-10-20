import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('QR page uses bounded local decoding and never fetches decoded URLs', async () => {
  const source = await readFile(new URL('../src/app/qr/page.tsx', import.meta.url), 'utf8');
  assert.ok(source.includes('MAX_FILE_BYTES = 10 * 1024 * 1024'));
  assert.ok(source.includes('MAX_PIXELS = 12_000_000'));
  assert.ok(source.includes('BarcodeDetector'));
  assert.ok(source.includes("import jsQR from 'jsqr'"));
  assert.ok(source.includes('jsQR(pixels.data, pixels.width, pixels.height'));
  assert.ok(source.includes('bundled cross-browser decoder'));
  assert.ok(source.includes('createImageBitmap'));
  assert.ok(source.includes('detector.detect(bitmap)'));
  assert.ok(source.includes('did not upload the image or open the payload'));
  assert.ok(source.includes("fetch('/api/analyze'"), 'URL text may be sent only to SATARK’s own analysis route');
  assert.ok(!source.includes('fetch(payload'), 'decoded destination must never be fetched');
  assert.ok(!source.includes('window.open'), 'decoded payload must not open a new destination automatically');
  assert.ok(!source.includes('location.href ='), 'decoded payload must not navigate the browser automatically');
  assert.ok(source.includes('async function copyPayload(payload: string)'), 'copy action must report its result');
  assert.ok(source.includes('Payload copied to clipboard.'), 'successful clipboard writes must be confirmed');
  assert.ok(source.includes('Select and copy the payload text above instead.'), 'clipboard failures must provide a usable fallback');
});

test('capability directory labels unported media tools honestly', async () => {
  const source = await readFile(new URL('../src/app/tools/page.tsx', import.meta.url), 'utf8');
  assert.ok(source.includes('QR-code investigation'));
  assert.ok(source.includes('PDF & text document review'));
  assert.ok(source.includes('Video frame sampling'));
  assert.ok(source.includes('OCR for scanned PDFs'));
  assert.ok(source.includes('does not analyze audio'));
});
