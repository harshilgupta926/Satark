export type BoundedJsonResult =
  | { ok: true; value: unknown }
  | { ok: false; status: 400 | 413; error: string };

/**
 * Parse JSON only after enforcing a byte limit against the actual request stream.
 * Content-Length is an early hint, never the sole limit for chunked requests.
 */
export async function readBoundedJson(request: Request, maxBytes: number): Promise<BoundedJsonResult> {
  const declared = request.headers.get('content-length');
  if (declared !== null) {
    if (!/^\d+$/.test(declared)) return { ok: false, status: 400, error: 'Invalid Content-Length.' };
    const length = Number(declared);
    if (!Number.isSafeInteger(length)) return { ok: false, status: 400, error: 'Invalid Content-Length.' };
    if (length > maxBytes) return { ok: false, status: 413, error: 'Request body is too large.' };
  }
  if (!request.body) return { ok: false, status: 400, error: 'A valid JSON object is required.' };
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let totalBytes = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      totalBytes += value.byteLength;
      if (totalBytes > maxBytes) {
        void reader.cancel().catch(() => undefined);
        return { ok: false, status: 413, error: 'Request body is too large.' };
      }
      chunks.push(value);
    }
  } catch {
    return { ok: false, status: 400, error: 'Could not read request body.' };
  } finally {
    reader.releaseLock();
  }
  try {
    const bytes = new Uint8Array(totalBytes);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
    return { ok: true, value: JSON.parse(text) as unknown };
  } catch {
    return { ok: false, status: 400, error: 'A valid JSON object is required.' };
  }
}
