"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useAuthStore } from "@/stores/auth-store";

export interface TimelineStepEvent {
  step: string;
  status: "in_progress" | "completed" | "failed";
  agent: string;
  title: string;
  description: string;
  latency_ms?: number;
  data?: Record<string, unknown>;
}

export type StreamStatus = "idle" | "connecting" | "streaming" | "completed" | "error";

export function useMissionStream() {
  const [missionId, setMissionId] = useState<string | null>(null);
  const [events, setEvents] = useState<TimelineStepEvent[]>([]);
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [completedData, setCompletedData] = useState<Record<string, unknown> | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const accessToken = useAuthStore((state) => state.accessToken);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const startStream = useCallback(
    (id: string) => {
      cleanup();
      setMissionId(id);
      setEvents([]);
      setError(null);
      setCompletedData(null);
      setStatus("connecting");

      const tokenParam = accessToken ? `?token=${encodeURIComponent(accessToken)}` : "";
      const streamUrl = `/api/v1/missions/${id}/stream${tokenParam}`;
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        setStatus("streaming");
      };

      es.addEventListener("timeline", (msg: MessageEvent) => {
        try {
          const payload = JSON.parse(msg.data) as TimelineStepEvent;
          setEvents((prev) => {
            // Replace or append step
            const idx = prev.findIndex((e) => e.step === payload.step);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = payload;
              return updated;
            }
            return [...prev, payload];
          });
        } catch (e) {
          console.error("Failed to parse SSE timeline event", e);
        }
      });

      es.addEventListener("done", (msg: MessageEvent) => {
        try {
          const data = JSON.parse(msg.data) as Record<string, unknown>;
          setCompletedData(data);
          setStatus("completed");
        } catch {
          setStatus("completed");
        }
        cleanup();
      });

      es.addEventListener("error", (msg: Event) => {
        // Check if custom error was dispatched
        if ("data" in msg && typeof (msg as MessageEvent).data === "string") {
          try {
            const errObj = JSON.parse((msg as MessageEvent).data) as { error?: string };
            setError(errObj.error || "Mission stream encountered an error");
          } catch {
            setError("Stream disconnected");
          }
        } else {
          // If already completed or events exists, close gracefully
          setStatus((prev) => (prev === "streaming" ? "completed" : "error"));
        }
        cleanup();
      });
    },
    [accessToken, cleanup]
  );

  const reset = useCallback(() => {
    cleanup();
    setMissionId(null);
    setEvents([]);
    setStatus("idle");
    setError(null);
    setCompletedData(null);
  }, [cleanup]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    missionId,
    events,
    status,
    error,
    completedData,
    startStream,
    reset,
  };
}
