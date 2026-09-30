import { useEffect, useState } from "react";
import { checkHealth } from "./api";
import { ChatWindow } from "./components/ChatWindow";
import { DocumentPanel } from "./components/DocumentPanel";
import { Navbar } from "./components/Navbar";
import "./index.css";

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // localStorage unavailable — fall through to OS preference
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [chatKey, setChatKey] = useState(0);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("theme", theme);
    } catch {
      // per-viewer convenience only — safe to ignore if storage is blocked
    }
  }, [theme]);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      const ok = await checkHealth();
      if (!cancelled) setConnected(ok);
    }
    poll();
    const interval = setInterval(poll, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="app">
      <Navbar
        theme={theme}
        onToggleTheme={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        onNewChat={() => setChatKey((k) => k + 1)}
        connected={connected}
      />
      <div className="app-body">
        <aside className="sidebar">
          <DocumentPanel />
        </aside>
        <main className="main">
          <ChatWindow key={chatKey} />
        </main>
      </div>
    </div>
  );
}
