import { useEffect, useState } from "react";
import { Today } from "./pages/Today";
import { Candidates } from "./pages/Candidates";

type Tab = "today" | "candidates";

export default function App() {
  const [tab, setTab] = useState<Tab>("today");
  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">CrossPilot</div>
        <nav className="tabs">
          <button className={tab === "today" ? "tab on" : "tab"} onClick={() => setTab("today")}>
            今日
          </button>
          <button
            className={tab === "candidates" ? "tab on" : "tab"}
            onClick={() => setTab("candidates")}
          >
            候选
          </button>
        </nav>
        <span className="badge">单人运行 · 样例数据</span>
      </header>
      <main className="page">{tab === "today" ? <Today /> : <Candidates />}</main>
    </div>
  );
}
