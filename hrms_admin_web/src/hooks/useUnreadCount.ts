import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { launchApi } from "@/lib/api/launch";

/**
 * Live unread-count subscription. Tries EventSource against
 * /api/v1/notifications/me/stream first; falls back to a 30s poll if
 * the stream fails (e.g. browser without EventSource, proxy that
 * doesn't pass-through SSE, or auth not yet established).
 */
export function useUnreadCount(): number {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let mounted = true;
    let es: EventSource | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;

    const startPolling = () => {
      if (pollTimer) return;
      const tick = async () => {
        if (!mounted) return;
        try {
          const n = await launchApi.unreadCount();
          if (mounted) setCount(n);
        } catch {
          /* swallow — keep retrying */
        }
      };
      void tick();
      pollTimer = setInterval(tick, 30_000);
    };

    try {
      const url = `${API_BASE_URL}/api/v1/notifications/me/stream`;
      es = new EventSource(url, { withCredentials: true });
      es.addEventListener("unread", (e) => {
        try {
          const data = JSON.parse((e as MessageEvent).data) as {
            unread: number;
          };
          if (mounted) setCount(data.unread ?? 0);
        } catch {
          /* malformed event, ignore */
        }
      });
      es.onerror = () => {
        es?.close();
        es = null;
        startPolling();
      };
    } catch {
      startPolling();
    }

    // Always do at least one initial fetch so the bell isn't blank during
    // the SSE handshake.
    void launchApi
      .unreadCount()
      .then((n) => {
        if (mounted) setCount(n);
      })
      .catch(() => {});

    return () => {
      mounted = false;
      if (es) es.close();
      if (pollTimer) clearInterval(pollTimer);
    };
  }, []);

  return count;
}
