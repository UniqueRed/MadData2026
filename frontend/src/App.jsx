import { useState, useCallback } from "react";
import CareGraph from "./components/CareGraph";
import VoiceOrb from "./components/VoiceOrb";
import ChatInput from "./components/ChatInput";
import NodeDetail from "./components/NodeDetail";
import CostSummary from "./components/CostSummary";
import { generatePathway, parseProfile, parseScenario } from "./services/api";
import "./App.css";

function App() {
  const [graph, setGraph] = useState(null);
  const [baselineGraph, setBaselineGraph] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [profile, setProfile] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([]);

  const addMessage = (role, text) => {
    setMessages((prev) => [...prev, { role, text }]);
  };

  const handleInput = useCallback(
    async (text) => {
      addMessage("user", text);
      setIsProcessing(true);

      try {
        if (!profile) {
          // First input: parse as patient profile
          const parsed = await parseProfile(text);
          if (parsed.error) {
            addMessage("system", parsed.error);
            setIsProcessing(false);
            return;
          }

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
          const pathway = await generatePathway(newProfile, [], 5);
          setGraph(pathway);
          setBaselineGraph(pathway);
          addMessage(
            "system",
            `Built your care pathway. ${pathway.nodes.length} health states mapped. 5-year projected out-of-pocket: $${Math.round(pathway.total_5yr_oop).toLocaleString()}.`
          );
        } else {
          // Subsequent inputs: parse as scenario/what-if
          const scenario = await parseScenario(text, profile.conditions);

          if (scenario.intent === "add_intervention" && scenario.interventions) {
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
            addMessage("system", "I understood your question. The graph shows the current projection based on your profile.");
          }
        }
      } catch (err) {
        addMessage("system", `Error: ${err.message}`);
      }

      setIsProcessing(false);
    },
    [profile, interventions, baselineGraph]
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1>CareGraph</h1>
        <span className="subtitle">Clinical-Financial Digital Twin</span>
      </header>

      <main className="app-main">
        <div className="graph-panel">
          <CareGraph graph={graph} onNodeSelect={setSelectedNode} />
        </div>

        <div className="side-panel">
          <CostSummary graph={graph} comparisonGraph={baselineGraph} />
          <NodeDetail node={selectedNode} />

          <div className="messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                {msg.text}
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <VoiceOrb onTranscript={handleInput} isProcessing={isProcessing} />
        <ChatInput onSubmit={handleInput} isProcessing={isProcessing} />
      </footer>
    </div>
  );
}

export default App;
