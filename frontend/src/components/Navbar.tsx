interface NavbarProps {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onNewChat: () => void;
  connected: boolean | null;
}

export function Navbar({ theme, onToggleTheme, onNewChat, connected }: NavbarProps) {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <span className="navbar-logo">R</span>
        <span>RAG Assistant</span>
      </div>

      <div className="navbar-actions">
        <div className="status" title={connected === null ? "Checking..." : connected ? "Backend reachable" : "Backend unreachable"}>
          <span
            className={`status-dot ${
              connected === null ? "" : connected ? "status-dot--online" : "status-dot--offline"
            }`}
          />
          {connected === false && <span>Offline</span>}
        </div>

        <button type="button" className="new-chat-btn" onClick={onNewChat}>
          New chat
        </button>

        <button
          type="button"
          className="icon-btn"
          onClick={onToggleTheme}
          aria-label="Toggle theme"
          title="Toggle theme"
        >
          {theme === "dark" ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
