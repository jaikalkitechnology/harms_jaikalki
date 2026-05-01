// Lazy Sentry initialiser — tolerant of the @sentry/react package being
// absent (e.g. during local dev when you haven't run `npm install` yet).
//
// Reads VITE_SENTRY_DSN at build time. Set it on a per-environment .env:
//   VITE_SENTRY_DSN=https://...@o1234.ingest.sentry.io/...
//   VITE_SENTRY_ENVIRONMENT=production
//   VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
//
// Imported lazily in main.tsx so the app boots even if @sentry/react is
// not installed.

export async function initSentry(): Promise<void> {
  const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;
  if (!dsn) return;
  try {
    const Sentry = await import("@sentry/react");
    Sentry.init({
      dsn,
      environment:
        (import.meta.env.VITE_SENTRY_ENVIRONMENT as string | undefined) ??
        (import.meta.env.MODE as string),
      release: (import.meta.env.VITE_APP_VERSION as string | undefined) ?? "dev",
      tracesSampleRate: Number(
        (import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE as string) ?? "0.1",
      ),
      // Don't send default PII — we have explicit user-id setting elsewhere.
      sendDefaultPii: false,
    });
    if (import.meta.env.DEV) console.info("[sentry] initialised");
  } catch (err) {
    if (import.meta.env.DEV)
      console.warn("[sentry] init skipped:", (err as Error).message);
  }
}
