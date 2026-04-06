import { useEffect, useState } from "react";
import { getStats } from "../api";

export default function Stats() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
    const id = setInterval(() => getStats().then(setStats).catch(() => {}), 10000);
    return () => clearInterval(id);
  }, []);

  const s = stats || {};
  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="value">{s.today_violations ?? "-"}</div>
        <div className="label">今日違規</div>
      </div>
      <div className="stat-card">
        <div className="value">{s.total_violations ?? "-"}</div>
        <div className="label">累計違規</div>
      </div>
      <div className="stat-card">
        <div className="value">{s.blacklist_count ?? "-"}</div>
        <div className="label">黑名單詞彙</div>
      </div>
      <div className="stat-card">
        <div className="value">{s.pending_count ?? "-"}</div>
        <div className="label">待審核詞彙</div>
      </div>
    </div>
  );
}
