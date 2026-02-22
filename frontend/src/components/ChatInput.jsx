import { useState } from "react";

export default function ChatInput({ onSubmit, isProcessing }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !isProcessing) {
      onSubmit(text.trim());
      setText("");
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={isProcessing ? "Thinking..." : "Describe your health profile or ask a what-if..."}
        disabled={isProcessing}
      />
      <button type="submit" disabled={!text.trim() || isProcessing} title="Send">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </form>
  );
}
