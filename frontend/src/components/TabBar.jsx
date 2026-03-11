export default function TabBar({ activeTab, onTabChange }) {
  const tabs = [
    {
      id: "simulate",
      label: "Simulate",
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="5" r="3" /><line x1="12" y1="8" x2="12" y2="14" /><line x1="12" y1="14" x2="6" y2="20" /><line x1="12" y1="14" x2="18" y2="20" />
        </svg>
      ),
    },
    {
      id: "compare",
      label: "Compare Plans",
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="3" width="20" height="18" rx="2" /><path d="M2 9h20" /><path d="M10 3v18" />
        </svg>
      ),
    },
  ];

  return (
    <nav className="tab-bar">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
