"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refresh: () => void;
}

/**
 * Fetch JSON from the (proxied) backend with optional polling. Keeps the last good
 * value on refresh so the UI never flashes an empty state mid-poll ("live" feel).
 */
export function useApi<T>(path: string | null, pollMs = 0): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const active = useRef(true);

  const load = useCallback(async () => {
    if (!path) return;
    try {
      const res = await fetch(path, { cache: "no-store" });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const json = (await res.json()) as T;
      if (active.current) {
        setData(json);
        setError(null);
      }
    } catch (e) {
      if (active.current) setError(e instanceof Error ? e.message : "request failed");
    } finally {
      if (active.current) setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    active.current = true;
    setLoading(true);
    load();
    if (pollMs > 0) {
      const id = setInterval(load, pollMs);
      return () => {
        active.current = false;
        clearInterval(id);
      };
    }
    return () => {
      active.current = false;
    };
  }, [load, pollMs]);

  return { data, error, loading, refresh: load };
}
