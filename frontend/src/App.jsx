import { useState, useCallback, useEffect, useRef } from "react";
import CareGraph from "./components/CareGraph";
import Dashboard from "./components/Dashboard";
import VoiceOrb from "./components/VoiceOrb";
import ChatInput from "./components/ChatInput";
import NodeDetail from "./components/NodeDetail";
import CostSummary from "./components/CostSummary";
import LandingPage from "./components/LandingPage";
import TabBar from "./components/TabBar";
import ComparePlans from "./components/ComparePlans";
import { generatePathway, parseProfile, parseScenario } from "./services/api";
import { useAuth } from "./contexts/AuthContext";
import "./App.css";

function App() {
  const { user, loading, signOut } = useAuth();
  const [currentView, setCurrentView] = useState("landing");
  const [graph, setGraph] = useState(null);
  const [baselineGraph, setBaselineGraph] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [profile, setProfile] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [simulateView, setSimulateView] = useState("tree");
  const [messages, setMessages] = useState([]);
  const [pendingProfile, setPendingProfile] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  useEffect(() => {
    if (!loading && !user && currentView !== "landing") {
      setCurrentView("landing");
    }
  }, [user, loading, currentView]);

  const addMessage = (role, text) => {
    setMessages((prev) => [...prev, { role, text }]);
  };

  const startNewProfile = useCallback(
    async (parsed) => {
      const symptom = parsed.symptom_conditions || [];
      const unmapped = parsed.unmapped_conditions || [];
      const newProfile = {
        age: parsed.age || 45,
        sex: parsed.sex || "M",
        conditions: parsed.conditions || [],
        insurance_type: parsed.insurance_type || "PPO",
        deductible: 2000,
        coinsurance: 0.2,
        oop_max: 8000,
      };

      setProfile(newProfile);
      setInterventions([]);
      setSelectedNode(null);
      const pathway = await generatePathway(newProfile, [], 5, symptom, unmapped);
      setGraph(pathway);
      setBaselineGraph(pathway);
      addMessage(
        "system",
        `Built your care pathway. ${pathway.nodes.length} health states mapped. 5-year projected out-of-pocket: $${Math.round(pathway.total_5yr_oop).toLocaleString()}.`
      );
    },
    []
  );

  const handleInput = useCallback(
    async (text) => {
      addMessage("user", text);
      setIsProcessing(true);

      try {
        // Handle pending new-profile confirmation
        if (pendingProfile) {
          const lower = text.toLowerCase().trim();
          const isYes = /^(y|yes|yeah|yep|sure|ok|okay|yea|start new)/.test(lower);
          const saved = pendingProfile;
          setPendingProfile(null);

          if (isYes) {
            setMessages([
              { role: "system", text: "Starting a new session..." },
            ]);
            await startNewProfile(saved);
          } else {
            addMessage("system", "Okay, keeping your current profile.");
          }
          setIsProcessing(false);
          return;
        }

        if (!profile) {
          // First message — parse as profile
          const parsed = await parseProfile(text);
          if (parsed.error) {
            addMessage("system", parsed.error);
            setIsProcessing(false);
            return;
          }
          if (parsed.off_topic) {
            addMessage("system", "Sorry, I can only help with health-related questions. Try describing your age, conditions, and insurance — like \"I'm a 45-year-old male with pre-diabetes and hypertension on a PPO plan.\"");
            setIsProcessing(false);
            return;
          }

          await startNewProfile(parsed);
        } else {
          // Profile exists — try scenario first
          const scenario = await parseScenario(text, profile.conditions);

          if (scenario.intent === "add_intervention" && scenario.interventions?.length) {
            const newInterventions = [
              ...new Set([...interventions, ...scenario.interventions]),
            ];
            setInterventions(newInterventions);
            const pathway = await generatePathway(profile, newInterventions, 5);
            setGraph(pathway);
            const savings = baselineGraph
              ? Math.round(baselineGraph.total_5yr_oop - pathway.total_5yr_oop)
              : 0;
            addMessage(
              "system",
              `Updated pathway with ${scenario.interventions.join(", ")}. ${savings > 0 ? `Estimated 5-year savings: $${savings.toLocaleString()}.` : ""}`
            );
          } else {
            // Not an intervention — check if it's a new profile
            const parsed = await parseProfile(text);
            if (!parsed.off_topic && !parsed.error && parsed.conditions?.length) {
              setPendingProfile(parsed);
              addMessage(
                "system",
                `It looks like you're describing a new patient (${parsed.age || "unknown age"}, ${parsed.conditions.join(", ")}). Would you like to start a new chat?`
              );
            } else if (scenario.off_topic) {
              addMessage("system", "Sorry, I can only help with health and cost-related questions. Try asking something like \"What if I start Metformin?\" or \"What's my biggest financial risk?\"");
            } else {
              addMessage("system", "I understood your question. The graph shows the current projection based on your profile.");
            }
          }
        }
      } catch (err) {
        addMessage("system", `Error: ${err.message}`);
      }

      setIsProcessing(false);
    },
    [profile, interventions, baselineGraph, pendingProfile, startNewProfile]
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1
          className="logo-link"
          onClick={() => setCurrentView("landing")}
        >
          miff
        </h1>
        <span className="subtitle">Clinical-Financial Digital Twin</span>
        <div className="header-spacer" />
        {currentView !== "landing" && (
          <TabBar
            activeTab={currentView}
            onTabChange={setCurrentView}
          />
        )}
        {user && (
          <div className="user-menu">
            <img
              className="user-avatar"
              src={user.user_metadata?.avatar_url}
              alt=""
              referrerPolicy="no-referrer"
            />
            <button className="sign-out-btn" onClick={signOut}>
              Sign Out
            </button>
          </div>
        )}
      </header>

      {currentView === "landing" && (
        <LandingPage onGetStarted={() => setCurrentView("simulate")} />
      )}

      {currentView === "simulate" && user && (
        <>
          <main className="app-main">
            <div className="graph-panel">
              {graph && (
                <div className="view-toggle">
                  <button
                    className={`view-toggle-btn${simulateView === "tree" ? " active" : ""}`}
                    onClick={() => setSimulateView("tree")}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="5" r="3" /><line x1="12" y1="8" x2="12" y2="14" /><line x1="12" y1="14" x2="6" y2="20" /><line x1="12" y1="14" x2="18" y2="20" />
                    </svg>
                    Visual
                  </button>
                  <button
                    className={`view-toggle-btn${simulateView === "dashboard" ? " active" : ""}`}
                    onClick={() => setSimulateView("dashboard")}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
                    </svg>
                    Dashboard
                  </button>
                </div>
              )}
              {simulateView === "tree" ? (
                <CareGraph graph={graph} onNodeSelect={setSelectedNode} />
              ) : (
                <Dashboard
                  graph={graph}
                  comparisonGraph={baselineGraph}
                  onNodeSelect={setSelectedNode}
                />
              )}
              {selectedNode && (
                <NodeDetail node={selectedNode} onClose={() => setSelectedNode(null)} />
              )}
            </div>

            <div className="side-panel">

              {graph && (
                <div className="side-section">
                  <CostSummary graph={graph} comparisonGraph={baselineGraph} />
                </div>
              )}

              <div className="side-section side-section-chat">
                <div className="section-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                  <span>Conversation</span>
                </div>
                <div className="messages">
                  {messages.length === 0 && !isProcessing && (
                    <div className="messages-empty">
                      <p>Describe your health profile below to get started.</p>
                    </div>
                  )}
                  {messages.map((msg, i) => (
                    <div key={i} className={`message ${msg.role}`}>
                      <div className="message-avatar">
                        {msg.role === "user" ? (
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>
                        ) : (
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        )}
                      </div>
                      <div className="message-content">{msg.text}</div>
                    </div>
                  ))}
                  {isProcessing && (
                    <div className="message system">
                      <div className="message-avatar">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                      </div>
                      <div className="message-content">
                        <span className="typing-indicator">
                          <span></span><span></span><span></span>
                        </span>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
                <div className="side-input">
                  <VoiceOrb onTranscript={handleInput} isProcessing={isProcessing} />
                  <ChatInput onSubmit={handleInput} isProcessing={isProcessing} />
                </div>
              </div>
            </div>
          </main>
        </>
      )}

      {currentView === "compare" && user && (
        <ComparePlans profile={profile} />
      )}
    </div>
  );
}

export default App;
