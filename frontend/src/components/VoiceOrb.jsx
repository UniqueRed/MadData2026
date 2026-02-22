import { useState, useRef, useCallback, useEffect } from "react";

const MAX_LISTEN_MS = 60000; // 1 minute max

export default function VoiceOrb({ onTranscript, isProcessing }) {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const timerRef = useRef(null);

  const stopListening = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, []);

  const startListening = useCallback(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      // Grab the latest final result
      const last = event.results[event.results.length - 1];
      if (last.isFinal) {
        const text = last[0].transcript;
        stopListening();
        if (onTranscript) onTranscript(text);
      }
    };

    recognition.onerror = () => {
      stopListening();
    };

    recognition.onend = () => {
      setIsListening(false);
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);

    // Auto-stop after 1 minute
    timerRef.current = setTimeout(() => {
      stopListening();
    }, MAX_LISTEN_MS);
  }, [onTranscript, stopListening]);

  return (
    <button
      className={`voice-orb ${isListening ? "listening" : ""} ${isProcessing ? "processing" : ""}`}
      onClick={isListening ? stopListening : startListening}
      disabled={isProcessing}
      title={isListening ? "Click to stop" : "Click to speak"}
    >
      <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      </svg>
    </button>
  );
}
