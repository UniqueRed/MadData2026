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
        placeholder="Describe your health profile or ask a what-if question..."
        disabled={isProcessing}
      />
      <button type="submit" disabled={!text.trim() || isProcessing}>
        Send
      </button>
    </form>
  );
}
