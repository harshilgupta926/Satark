/** Validate the Supabase endpoint before forwarding a user's bearer token.
 *
 * Hosted Supabase projects remain the default. Self-hosted HTTPS endpoints require an
 * explicit deployment opt-in. Plain HTTP is accepted only for known local development
 * hosts and only when a second explicit opt-in is enabled.
 */
const LOCAL_HTTP_HOSTS = new Set([
  "localhost",
  "127.0.0.1",
  "::1",
  "host.docker.internal",
  "supabase-kong",
  "kong",
]);

export function isAllowedSupabaseEndpoint(url: URL): boolean {
  if (url.username || url.password || url.search || url.hash) return false;

  const hostname = url.hostname.toLowerCase();
  if (url.protocol === "https:") {
    return hostname.endsWith(".supabase.co")
      || process.env.SATARK_SUPABASE_ALLOW_SELF_HOSTED === "true";
  }

  return url.protocol === "http:"
    && process.env.SATARK_ALLOW_INSECURE_LOCAL_SUPABASE === "true"
    && LOCAL_HTTP_HOSTS.has(hostname);
}
