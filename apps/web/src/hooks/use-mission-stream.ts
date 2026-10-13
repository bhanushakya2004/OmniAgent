"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useCartStore } from "@/stores/cart-store";
import { getOrCreateGuestSessionId, API_BASE_URL } from "@/lib/api-client";

export interface StreamEvent {
  sequence_id: number;
  event_type:
    | "agent_thought"
    | "tool_call"
    | "tool_result"
    | "basket_update"
    | "grounding_check"
    | "wayfinding_route"
    | "mission_complete"
    | "error"
    | string;
  payload: Record<string, unknown>;
  created_at?: string;
}

export type StreamStatus = "idle" | "connecting" | "streaming" | "completed" | "error";

export function useMissionStream() {
  const [missionId, setMissionId] = useState<string | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [completedData, setCompletedData] = useState<Record<string, unknown> | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const lastSeqRef = useRef<number>(0);
  const accessToken = useAuthStore((state) => state.accessToken);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const handleIncomingEvent = useCallback((eventType: string, dataStr: string, eventIdStr?: string) => {
    try {
      const payload = JSON.parse(dataStr) as Record<string, unknown>;
      const seqId = eventIdStr ? parseInt(eventIdStr, 10) : lastSeqRef.current + 1;
      if (!isNaN(seqId) && seqId > lastSeqRef.current) {
        lastSeqRef.current = seqId;
      }

      const newEvent: StreamEvent = {
        sequence_id: isNaN(seqId) ? lastSeqRef.current : seqId,
        event_type: eventType,
        payload,
      };

      setEvents((prev) => {
        // Prevent duplicate sequence IDs
        if (prev.some((e) => e.sequence_id === newEvent.sequence_id && e.event_type === newEvent.event_type)) {
          return prev;
        }
        return [...prev, newEvent];
      });

      // React to specific event types
      if (eventType === "basket_update") {
        useCartStore.getState().fetchCart();
      } else if (eventType === "mission_complete") {
        setCompletedData(payload);
        setStatus("completed");
        useCartStore.getState().fetchCart();
      } else if (eventType === "error") {
        setError(typeof payload.error === "string" ? payload.error : "Mission execution error");
        setStatus("error");
      }
    } catch (e) {
      console.error("Failed to parse SSE payload", e, dataStr);
    }
  }, []);

  const startStream = useCallback(
    (id: string) => {
      cleanup();
      setMissionId(id);
      setEvents([]);
      setError(null);
      setCompletedData(null);
      lastSeqRef.current = 0;
      setStatus("connecting");

      const guestId = getOrCreateGuestSessionId();
      const params = new URLSearchParams();
      if (accessToken) {
        params.set("token", accessToken);
      }
      if (guestId) {
        params.set("guest_session_id", guestId);
      }
      if (lastSeqRef.current > 0) {
        params.set("after_seq", lastSeqRef.current.toString());
      }

      const streamUrl = `${API_BASE_URL}/api/v1/missions/${id}/stream?${params.toString()}`;
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        setStatus("streaming");
      };

      const eventTypes = [
        "agent_thought",
        "tool_call",
        "tool_result",
        "basket_update",
        "grounding_check",
        "wayfinding_route",
        "mission_complete",
        "error",
        "timeline",
        "done",
      ];

      eventTypes.forEach((t) => {
        es.addEventListener(t, (msg: MessageEvent) => {
          handleIncomingEvent(t, msg.data, msg.lastEventId);
          if (t === "done" || t === "mission_complete") {
            cleanup();
          }
        });
      });

      // Default message listener
      es.onmessage = (msg: MessageEvent) => {
        handleIncomingEvent("message", msg.data, msg.lastEventId);
      };

      es.onerror = () => {
        // If already completed, gracefully close
        if (lastSeqRef.current > 0 && status === "streaming") {
          // Reconnect attempt or completed
        } else {
          setStatus((prev) => (prev === "completed" ? "completed" : "error"));
        }
      };
    },
    [accessToken, cleanup, handleIncomingEvent, status]
  );

  const reset = useCallback(() => {
    cleanup();
    setMissionId(null);
    setEvents([]);
    setStatus("idle");
    setError(null);
    setCompletedData(null);
    lastSeqRef.current = 0;
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
