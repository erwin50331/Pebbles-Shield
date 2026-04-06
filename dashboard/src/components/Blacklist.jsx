import { useEffect, useState } from "react";
import { getBlacklist, addToBlacklist, deleteFromBlacklist } from "../api";

export default function Blacklist() {
  const [items, setItems] = useState([]);
  const [newWord, setNewWord] = useState("");

  const load = () => getBlacklist().then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    const w = newWord.trim();
    if (!w) return;
    await addToBlacklist(w, "manual");
    setNewWord("");
    load();
  };

  const handleDelete = async (word) => {
    if (!confirm(`確定要從黑名單移除「${word}」？`)) return;
    await deleteFromBlacklist(word);
    load();
  };

  return (
    <div>
      <div className="input-row">
        <input
          type="text"
          placeholder="輸入新詞彙..."
          value={newWord}
          onChange={e => setNewWord(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleAdd()}
        />
        <button className="btn btn-blue" onClick={handleAdd}>新增</button>
      </div>

      {items.length === 0
        ? <div className="empty">黑名單是空的</div>
        : (
          <div className="card">
            <table>
              <thead>
                <tr>
                  <th>詞彙</th>
                  <th>類別</th>
                  <th>加入時間</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map(w => (
                  <tr key={w.id}>
                    <td><strong>{w.word}</strong></td>
                    <td><span className="badge badge-gray">{w.category}</span></td>
                    <td style={{ color: "#718096", fontSize: "0.8rem" }}>
                      {new Date(w.added_at).toLocaleString("zh-TW")}
                    </td>
                    <td>
                      <button className="btn btn-red" onClick={() => handleDelete(w.word)}>移除</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    </div>
  );
}
