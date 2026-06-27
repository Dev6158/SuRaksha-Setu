interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const tabs = [
    { id: "dashboard", label: "📊 Dashboard" },
    { id: "upload", label: "📤 Upload Asset" },
    { id: "analytics", label: "📈 Analytics" },
    { id: "documents", label: "📄 Documents" },
    { id: "settings", label: "⚙️ Settings" },
  ];

  return (
    <div className="w-64 bg-slate-950 text-white p-6 flex flex-col border-r border-slate-800">
      <div className="flex items-center space-x-2 mb-8">
        <span className="text-2xl">🛡️</span>
        <h1 className="text-xl font-bold tracking-tight text-white">
          SuRaksha Setu
        </h1>
      </div>

      <ul className="space-y-2 flex-grow">
        {tabs.map((tab) => (
          <li
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`p-3 rounded-lg cursor-pointer transition-all duration-150 ${
              activeTab === tab.id
                ? "bg-slate-800 text-blue-400 font-semibold border-l-4 border-blue-500"
                : "hover:bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </li>
        ))}
      </ul>

      <div className="text-xs text-slate-600 border-t border-slate-900 pt-4">
        Canara SuRaksha 2.0<br />
        <span className="text-slate-700">Prototype Phase (Offline)</span>
      </div>
    </div>
  );
}