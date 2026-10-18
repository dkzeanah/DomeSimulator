// Public chat: everyone in the world reads it; members write it. The site keeps the messages
// (D1, /api/game/chat) and staff can remove one. Polled every few seconds while the world is open.

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../lib/api";

export interface ChatMessage { id: number; name: string; text: string; at: string; staff: boolean }

export function useChat(active: boolean) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const last = useRef(0);
  const poll = useCallback(async () => {
    try {
      const r = await api<{ messages: ChatMessage[] }>(`/game/chat?after=${last.current}`);
      if (r.messages.length) {
        last.current = r.messages[r.messages.length - 1].id;
        setMessages((m) => [...m, ...r.messages].slice(-100));
      }
      setError(null);
    } catch (e) { setError((e as Error).message); }
  }, []);
  useEffect(() => {
    if (!active) return;
    void poll();
    const t = window.setInterval(poll, 4000);
    return () => window.clearInterval(t);
  }, [active, poll]);
  const send = useCallback(async (text: string) => {
    await api("/game/chat", { body: { text } });
    await poll();
  }, [poll]);
  return { messages, send, error };
}
