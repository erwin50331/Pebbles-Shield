import { useEffect, useState } from "react";
import { getPending, approveWord, rejectWord } from "../api";

export default function Pending() {
  const [items, setItems] = useState([]);

  const load = () => getPending().then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const handle = async (word, action) => {
    if (action === "approve") await approveWord(word);
    else await rejectWord(word);
    load();
  };

  const riskBadge = (score) => {
    if (score >= 0.7) return <span className="badge badge-red">高風險 {score.toFixed(2)}</span>;
    if (score >= 0.4) return <span className="badge badge-yellow">中風險 {score.toFixed(2)}</span>;
    return <span className="badge badge-green">低風險 {score.toFixed(2)}</span>;
  };

  if (items.length === 0) return <div className="empty">沒有待審核詞彙</div>;

  return (
    <div className="card">
      <p style={{ color: "#718096", marginBottom: 12, fontSize: "0.85rem" }}>
        審核通過 → 自動加入黑名單。標記誤報 → 從待審核移除。
      </p>
      <table>
        <thead>
          <tr>
            <th>詞彙</th>
            <th>來源</th>
            <th>出現次數</th>
            <th>風險評分</th>
            <th>分析說明</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {items.map(w => (
            <tr key={w.id}>
              <td><strong>{w.word}</strong></td>
              <td><span className="badge badge-gray">{w.source}</span></td>
              <td>{w.frequency}</td>
              <td>{riskBadge(w.risk_score)}</td>
              <td style={{ color: "#a0aec0", fontSize: "0.85rem" }}>{w.risk_reason || "尚未分析"}</td>
              <td style={{ display: "flex", gap: 6 }}>
                <button className="btn btn-green" onClick={() => handle(w.word, "approve")}>加入黑名單</button>
                <button className="btn btn-gray" onClick={() => handle(w.word, "reject")}>誤報</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
