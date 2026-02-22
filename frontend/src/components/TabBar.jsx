export default function TabBar({ activeTab, onTabChange }) {
  const tabs = [
    { id: "simulate", label: "Simulate" },
    { id: "compare", label: "Compare Plans" },
  ];

  return (
    <nav className="tab-bar">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
