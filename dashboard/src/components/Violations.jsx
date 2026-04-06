import { useEffect, useState } from "react";
import { getViolations } from "../api";

export default function Violations({ defenseMode }) {
  const [items, setItems] = useState([]);

  useEffect(() => {
    getViolations().then(setItems).catch(() => {});
    const id = setInterval(() => getViolations().then(setItems).catch(() => {}), 10000);
    return () => clearInterval(id);
  }, []);

  if (items.length === 0) return <div className="empty">目前沒有違規紀錄</div>;

  return (
    <div className="card">
      <table>
        <thead>
          <tr>
            <th>時間</th>
            <th>使用者</th>
            <th>頻道</th>
            <th>命中詞彙</th>
            <th>訊息內容</th>
          </tr>
        </thead>
        <tbody>
          {items.map(v => (
            <tr key={v.id}>
              <td style={{ whiteSpace: "nowrap", color: "#718096", fontSize: "0.8rem" }}>
                {new Date(v.detected_at).toLocaleString("zh-TW")}
              </td>
              <td>{v.username}</td>
              <td style={{ color: "#718096" }}>{v.channel_id}</td>
              <td>
                {v.matched_words.split(",").map(w => (
                  <span key={w} className="badge badge-red" style={{ marginRight: 4 }}>{w}</span>
                ))}
              </td>
              <td>
                {defenseMode
                  ? <span className="masked">[偵測到違規內容 — 心理防禦模式已遮蔽]</span>
                  : <span style={{ wordBreak: "break-all" }}>{v.message_content}</span>
                }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
