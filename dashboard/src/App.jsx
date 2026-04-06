import { useState } from "react";
import Stats from "./components/Stats";
import Violations from "./components/Violations";
import Blacklist from "./components/Blacklist";
import Pending from "./components/Pending";
import "./App.css";

const TABS = [
  { id: "violations", label: "違規紀錄" },
  { id: "pending", label: "待審核詞彙" },
  { id: "blacklist", label: "黑名單管理" },
];

export default function App() {
  const [tab, setTab] = useState("violations");
  const [defenseMode, setDefenseMode] = useState(false);

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <img src="/logo.png" alt="logo" className="header-logo" />
          <div>
            <h1>鵝卵石之盾</h1>
            <span className="subtitle">PEBBLES SHIELD</span>
          </div>
        </div>
        <div className="header-right">
          <label className="defense-toggle">
            <input
              type="checkbox"
              checked={defenseMode}
              onChange={e => setDefenseMode(e.target.checked)}
            />
            <span className={defenseMode ? "defense-on" : ""}>
              {defenseMode ? "心理防禦模式：開啟" : "心理防禦模式：關閉"}
            </span>
          </label>
        </div>
      </header>

      <Stats />

      <nav className="tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="content">
        {tab === "violations" && <Violations defenseMode={defenseMode} />}
        {tab === "pending" && <Pending />}
        {tab === "blacklist" && <Blacklist />}
      </main>
    </div>
  );
}
